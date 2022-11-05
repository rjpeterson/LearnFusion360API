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
    nonRound = True if butted or bladed else False
    threadLength = 1.0 # cm
    headDepth = 0.15 # cm
    jBendData = {
        "headOffest": .305, # cm
        "bendRadius": .3375, # cm
    }
    if  straightPull:
        adjustedLength = length + headDepth
    else:
        adjustedLength = length - jBendData['bendRadius'] + (diameter / 2)

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
    pathSketch.name = 'pathSketch'
    pathArcs = pathSketch.sketchCurves.sketchArcs
    pathLines = pathSketch.sketchCurves.sketchLines

    # Sketch the path for spoke length and j-bend
    if straightPull:
        shaftStart = newPoint(0,0,0)
        shaftEnd = newPoint(adjustedLength, 0, 0)
    else:
        head = pathLines.addByTwoPoints(newPoint(0,0,0), newPoint(jBendData['headOffest'], 0, 0))
        bendCenter = newPoint(jBendData['headOffest'], jBendData['bendRadius'], 0)
        jBend = pathArcs.addByCenterStartSweep(bendCenter, head.endSketchPoint, pi / 2)
        vector = core.Vector3D.create(0, adjustedLength, 0)
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
    profileSketch.name = ' base diameter sketch'
    profileCircles = profileSketch.sketchCurves.sketchCircles
    profileCircles.addByCenterRadius(newPoint(0,0,0), diameter / 2)
    bodyProfile = profileSketch.profiles.item(0)

    # Extrude a cylinder along the path
    sweeps = newComp.features.sweepFeatures
    sweepInput = sweeps.createInput(bodyProfile, path, fusion.FeatureOperations.NewBodyFeatureOperation)
    if nonRound: # Sweep to start of first taper
        sweepInput.distanceOne = core.ValueInput.createByReal(1.5 / adjustedLength)

    # Sweep first body section
    spokeBody = sweeps.add(sweepInput)

    if not nonRound:
        # Get face that threads will later be applied to
        tipFace = spokeBody.endFaces.item(0)
        for face in spokeBody.sideFaces:
            for edge in face.edges:
                if edge == tipFace.edges.item(0):
                    threadFace = face
                    break

    if nonRound:
        profile1 = spokeBody.endFaces.item(0) # Profile 1 (wide end of first taper)

        distance = core.ValueInput.createByReal(1.0)
        endPlaneInput: fusion.ConstructionPlaneInput = newComp.constructionPlanes.createInput()
        endPlaneInput.setByDistanceOnPath(path, distance)
        endPlane = newComp.constructionPlanes.add(endPlaneInput)
        endSketch: fusion.Sketch = sketches.add(endPlane)
        endSketch.name = 'endSketch'
        endSketch.sketchCurves.sketchCircles.addByCenterRadius(newPoint(0,0,0), diameter / 2)
        profile5 = endSketch.profiles.item(0) # Profile 5 (tip of spoke)

        extrudes = newComp.features.extrudeFeatures
        endExtrudeInput = extrudes.createInput(profile5, fusion.FeatureOperations.NewBodyFeatureOperation)
        endExtrudeDistance = fusion.DistanceExtentDefinition.create(core.ValueInput.createByString('15 mm'))
        endExtrudeInput.setOneSideExtent(endExtrudeDistance, fusion.ExtentDirections.NegativeExtentDirection)
        endExtrude = extrudes.add(endExtrudeInput) # end section

        tipFace = endExtrude.startFaces.item(0)
        profile4 = endExtrude.endFaces.item(0) # Profile 4 (wide end of second taper)
        threadFace = endExtrude.sideFaces.item(0)

        taper1PlaneInput: fusion.ConstructionPlaneInput = newComp.constructionPlanes.createInput()
        taper1PlaneInput.setByOffset(spokeBody.endFaces.item(0), core.ValueInput.createByString('10 mm'))
        taper1Plane = newComp.constructionPlanes.add(taper1PlaneInput)
        taper1Sketch: fusion.Sketch = sketches.add(taper1Plane)
        taper1Sketch.name = 'taper1Sketch'

        taper2PlaneInput: fusion.ConstructionPlaneInput = newComp.constructionPlanes.createInput()
        taper2PlaneInput.setByOffset(profile4, core.ValueInput.createByString('10 mm'))
        taper2Plane = newComp.constructionPlanes.add(taper2PlaneInput)
        taper2Sketch: fusion.Sketch = sketches.add(taper2Plane)
        taper2Sketch.name = 'taper2Sketch'

        if butted:
            taper1Sketch.sketchCurves.sketchCircles.addByCenterRadius(newPoint(0, 0, 0), diameter * .375)
            profile2 = taper1Sketch.profiles.item(0) # Profile 2 (thin end of first taper)
            taper2Sketch.sketchCurves.sketchCircles.addByCenterRadius(newPoint(0,0,0), diameter * .375)
            profile3 = taper2Sketch.profiles.item(0) # Profile 3 (thin end of first taper)
        if bladed:
            taper1Sketch.sketchCurves.sketchLines.addTwoPointRectangle(newPoint(0.045, .11, 0), newPoint(-0.045, -.11, 0))
            profile2 = taper1Sketch.profiles.item(0) # Profile 2 (flat end of first taper)
            taper2Sketch.sketchCurves.sketchLines.addTwoPointRectangle(newPoint(0.045, .11, 0), newPoint(-0.045, -.11, 0))
            profile3 = taper2Sketch.profiles.item(0) # Profile 2 (flat end of first taper)

        lofts = newComp.features.loftFeatures
        taper1Input = lofts.createInput(fusion.FeatureOperations.JoinFeatureOperation)
        taper1Input.loftSections.add(profile1)
        taper1Input.loftSections.add(profile2)
        taper1Loft = lofts.add(taper1Input) # first tapered section

        centerLoftInput = lofts.createInput(fusion.FeatureOperations.JoinFeatureOperation)
        centerLoftInput.loftSections.add(profile2)
        centerLoftInput.loftSections.add(profile3)
        centerLoft = lofts.add(centerLoftInput) # center section

        taper2Input = lofts.createInput(fusion.FeatureOperations.JoinFeatureOperation)
        taper2Input.loftSections.add(profile3)
        taper2Input.loftSections.add(profile4)
        taper2Loft = lofts.add(taper2Input) # second tapered section
        

    # Sketch the spoke head revolve profile
    headSketch = fusion.Sketch.cast(sketches.add(xZPlane))
    headArcs = headSketch.sketchCurves.sketchArcs
    headLines = headSketch.sketchCurves.sketchLines
    point1 = newPoint(0, -diameter / 2, 0)
    point2 = newPoint(headDepth, -diameter / 2, 0)
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
    planeInput: fusion.ConstructionPlaneInput = newComp.constructionPlanes.createInput()
    planeInput.setByOffset(tipFace, core.ValueInput.createByReal(-threadLength))
    threadStartPlane = newComp.constructionPlanes.add(planeInput)
    threadStartPlane.name = 'threadStartPlane'
    
    # Get SplitFaceFetures
    splitFaceFeats = rootComp.features.splitFaceFeatures
    
    # Set faces to split
    facesCol = core.ObjectCollection.create()
    facesCol.add(threadFace)
    
    # Create a split face feature of surface intersection split type
    splitFaceInput = splitFaceFeats.createInput(facesCol, threadStartPlane, True)
    split = splitFaceFeats.add(splitFaceInput)
    
    # Get face to add threads to
    entity = split.faces.item(0)

    # define the thread input with the lenght 10 mm
    threadInput = threads.createInput(entity, threadInfo)
    threadInput.isFullLength = False
    threadInput.threadLength = core.ValueInput.createByReal(threadLength)
    
    # create the thread
    thread = threads.add(threadInput)

    newComp.isConstructionFolderLightBulbOn = False