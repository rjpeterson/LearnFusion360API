from math import pi
import os
import adsk
import adsk.core as core
import adsk.fusion as fusion
from ...lib import fusion360utils as futil

app = core.Application.get()
if app:
    ui = app.userInterface
    createPoint = core.Point3D.create
    alert = ui.messageBox
design = fusion.Design.cast(app.activeProduct)
if not design:
    alert('You must be in the design workspace to use this command')
skipValidate = False


class SpokeLogic():
    def __init__(self) -> None:
        self.length = 30
        self.diameter = 0.2
        self.butted = False
        self.straightPull = False
        self.bladed = False
    
    def CreateCommandInputs(self, inputs: core.CommandInputs):
        global skipValidate
        skipValidate = True

        self.lengthInput: core.ValueCommandInput = inputs.addValueInput('length', 'Length', 'mm', core.ValueInput.createByReal(self.length))
        self.buttedInput: core.BoolValueCommandInput = inputs.addBoolValueInput('butted', 'Butted', True, '', self.butted)
        self.straightPullInput: core.BoolValueCommandInput = inputs.addBoolValueInput('straightPull', 'Straight Pull', True, '', self.straightPull)
        self.bladedInput: core.BoolValueCommandInput = inputs.addBoolValueInput('bladed', 'Bladed', True, '', self.bladed)
        drop_down_style = core.DropDownStyles.TextListDropDownStyle
        self.diameterInput: core.DropDownCommandInput = inputs.addDropDownCommandInput('diameter', 'Diameter', drop_down_style)
        self.diameterInput.listItems.add('1.8 mm', False)
        self.diameterInput.listItems.add('2.0 mm', True)
        self.diameterInput.listItems.add('2.3 mm', False)
        self.diameterInput.listItems.add('2.6 mm', False)

        self.errorMessageTextInput = inputs.addTextBoxCommandInput('errMessage', '', '', 2, True)
        self.errorMessageTextInput.isFullWidth = True

        skipValidate = False

    def HandleInputsChanged(self, args: core.InputChangedEventArgs):
        changedInput = args.input
        
        if not skipValidate:
            if changedInput.id == 'butted':
                if self.buttedInput.value == True:
                    self.bladedInput.isVisible = False
                    self.bladedInput.value = False
                else:
                    self.bladedInput.isVisible = True
            elif changedInput.id == 'bladed':
                if self.bladedInput.value == True:
                    self.buttedInput.isVisible = False
                    self.buttedInput.value = False
                else:
                    self.buttedInput.isVisible = True

    def HandleValidateInputs(self, args: core.ValidateInputsEventArgs):
        unitsMgr = design.unitsManager
        if not skipValidate:
            self.errorMessageTextInput.text = ''
            if not self.lengthInput.isValidExpression:
                self.errorMessageTextInput.text = 'The spoke length is invalid'
                args.areInputsValid = False
                return
                     
            if self.lengthInput.value < 10 or self.lengthInput.value > 50:
                self.errorMessageTextInput.text = 'The spoke length should be between 100 and 500 mm'
                args.areInputsValid = False
                return
            if self.bladedInput.value == True and self.buttedInput.value == True:
                self.errorMessageTextInput.text = 'Bladed and Butted cannot both be checked'
                args.areInputsValid = False
                return
            args.areInputsValid = True
            self.bladed = self.bladedInput.value
            self.butted = self.buttedInput.value
            self.length = unitsMgr.evaluateExpression(self.lengthInput.expression)
            self.diameter = unitsMgr.evaluateExpression(self.diameterInput.selectedItem.name)
            self.straightPull = self.straightPullInput.value

    def HandleExecute(self, args: core.CommandEventArgs):
        createSpoke(
            self.bladed,
            self.butted,
            self.diameter,
            self.length,
            self.straightPull
        )

def createSpoke(bladed: bool, butted: bool, diameter: float, length: int, straightPull: bool):
    threadLength = 10 # mm
    jBendData = {
        "headOffest": .305,
        "bendRadius": .3375,
    }
    # headDiameter = 0.40

    alert = ui.messageBox
    newPoint = core.Point3D.create
    rootComp = design.rootComponent

    # Create a new component by creating an occurrence.
    occurence = rootComp.occurrences.addNewComponent(core.Matrix3D.create())
    newComp = occurence.component
    newComp.name = f'Spoke {diameter} x {length}'

    sketches = newComp.sketches
    xYPlane = newComp.xYConstructionPlane
    xZPlane = newComp.xZConstructionPlane
    pathSketch = fusion.Sketch.cast(sketches.add(xYPlane))
    pathArcs = pathSketch.sketchCurves.sketchArcs
    pathLines = pathSketch.sketchCurves.sketchLines

    # Sketch the path for spoke length and j-bend
    if straightPull:
        shaftStart = newPoint(0,0,0)
        shaftEnd = newPoint(length, 0, 0)
    else:
        head = pathLines.addByTwoPoints(newPoint(0,0,0), newPoint(jBendData['headOffest'], 0, 0))
        bendCenter = newPoint(jBendData['headOffest'], jBendData['bendRadius'], 0)
        jBend = pathArcs.addByCenterStartSweep(bendCenter, head.endSketchPoint, pi / 2)
        vector = core.Vector3D.create(0, length, 0)
        transform = core.Matrix3D.create()
        transform.translation = vector
        pointToCopy = core.ObjectCollection.create()
        pointToCopy.add(jBend.endSketchPoint)
        pointCopy: core.ObjectCollection = pathSketch.copy(pointToCopy, transform)
        shaftStart = jBend.endSketchPoint
        shaftEnd = pointCopy.item(0)
    shaft = pathLines.addByTwoPoints(shaftStart, shaftEnd)
    # curveCollection = core.ObjectCollection.create()
    # curveCollection.add(head)
    # curveCollection.add(jBend)
    # curveCollection.add(shaft)
    path = newComp.features.createPath(shaft, True)

    # Sketch the spoke body profile
    distance = core.ValueInput.createByReal(0.0)
    planeInput: fusion.ConstructionPlaneInput = newComp.constructionPlanes.createInput()
    planeInput.setByDistanceOnPath(path, distance)
    profilePlane = newComp.constructionPlanes.add(planeInput)
    profileSketch = fusion.Sketch.cast(newComp.sketches.add(profilePlane))
    profileCircles = profileSketch.sketchCurves.sketchCircles
    profileCircles.addByCenterRadius(newPoint(0,0,0), diameter / 2)
    bodyProfile = profileSketch.profiles.item(0)

    # Extrude a cylinder along the path
    sweeps = newComp.features.sweepFeatures
    sweepInput = sweeps.createInput(bodyProfile, path, fusion.FeatureOperations.NewBodyFeatureOperation)
    spokeBody = sweeps.add(sweepInput)

    # Sketch the spoke head revolve profile
    headSketch = fusion.Sketch.cast(sketches.add(xZPlane))
    headArcs = headSketch.sketchCurves.sketchArcs
    headLines = headSketch.sketchCurves.sketchLines
    point1 = newPoint(0, -diameter / 2, 0)
    point2 = newPoint(.15, -diameter / 2, 0)
    arcCenter = newPoint(.1071, -diameter / 2, 0)
    arc = headArcs.addByCenterStartSweep(arcCenter, point1, pi / 2)
    headLines.addByTwoPoints(arc.endSketchPoint, point2)
    headLines.addByTwoPoints(point2, point1)

    # Get revolve profile
    headProfile = headSketch.profiles.item(0)
    if not headProfile:
        alert('Could not find head profile')

    # Revolve the profile
    revolves = newComp.features.revolveFeatures
    revolveInput = revolves.createInput(headProfile, newComp.xConstructionAxis, fusion.FeatureOperations.JoinFeatureOperation)
    angle = core.ValueInput.createByReal(2 * pi)
    revolveInput.setAngleExtent(True, angle)
    revolves.add(revolveInput)

    # Add threads to end
    threads = newComp.features.threadFeatures
    threadDataQuery = threads.threadDataQuery
    threadTypes = threadDataQuery.allThreadTypes
    threadType = threadTypes[10]
    
    allsizes = threadDataQuery.allSizes(threadType)
    threadSize = allsizes[19]
    
    allDesignations = threadDataQuery.allDesignations(threadType, threadSize)
    threadDesignation = allDesignations[0]
    
    allClasses = threadDataQuery.allClasses(False, threadType, threadDesignation)
    threadClass = allClasses[0]

    # create the threadInfo according to the query result
    threadInfo = threads.createThreadInfo(False, threadType, threadDesignation, threadClass)
    
    # get the face the thread will be applied to
    futil.log(f'spokeBody has {len(spokeBody.sideFaces)} faces')
    endCap = spokeBody.endFaces.item(0)
    planeInput: fusion.ConstructionPlaneInput = newComp.constructionPlanes.createInput()
    planeInput.setByOffset(endCap, core.ValueInput.createByString(f'-{threadLength} mm'))
    threadStartPlane = newComp.constructionPlanes.add(planeInput)
    for face in endCap.edges.item(0).faces:
        if face.entityToken != endCap.entityToken:
            faceToSplit = face
            break
    
    # Get SplitFaceFetures
    splitFaceFeats = rootComp.features.splitFaceFeatures
    
    # Set faces to split
    facesCol = core.ObjectCollection.create()
    facesCol.add(faceToSplit)
    
    # Create a split face feature of surface intersection split type
    splitFaceInput = splitFaceFeats.createInput(facesCol, threadStartPlane, True)
    split = splitFaceFeats.add(splitFaceInput)
    
    # Get face to add threads to
    for face in split.faces:
        if endCap.edges.item(0) in face.edges:
            entity = face
            break

    # define the thread input with the lenght 10 mm
    threadInput = threads.createInput(entity, threadInfo)
    threadInput.isFullLength = False
    threadInput.threadLength = core.ValueInput.createByString(f'{threadLength} mm')
    
    # create the thread
    thread = threads.add(threadInput)

    newComp.isConstructionFolderLightBulbOn = False