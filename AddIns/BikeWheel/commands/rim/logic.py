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

# Rim profiles only list points for one half of the rim, The profile must be mirrored and then extruded for a complete rim body
rimProfiles = {
    'VO Enterprise': {
        'profile': '/rim_profiles/VO_Enterprise.dxf',
        'sizes': {
            '700c': 60.52,
            '27': 61.27
        }
    },
    'testRim': {
        'profile': '/rim_profiles/testRim.dxf',
        'sizes': {
            '24': 23.0,
            '650b': 59.2
        }
    }
}

class RimLogic():
    @property
    def resource_dir(self):
        try:
            _resource_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')
            return _resource_dir if os.path.isdir(_resource_dir) else ''
        except:
            return ''

    def __init__(self) -> None:
        self.rim = 'VO Enterprise'
        self.size = '700c'
        self.spokes = 32
    
    def CreateCommandInputs(self, inputs: core.CommandInputs):
        global skipValidate
        skipValidate = True

        drop_down_style = core.DropDownStyles.TextListDropDownStyle
        self.rimInput: core.DropDownCommandInput = inputs.addDropDownCommandInput('rim', 'Rim', drop_down_style)
        self.sizeInput: core.DropDownCommandInput = inputs.addDropDownCommandInput('size', 'Size', drop_down_style)
        self.spokesInput: core.RadioButtonGroupCommandInput = inputs.addRadioButtonGroupCommandInput('spokes', 'Spokes')

        self.spokesInput.listItems.add('24', False)
        self.spokesInput.listItems.add('28', False)
        self.spokesInput.listItems.add('32', True)
        self.spokesInput.listItems.add('36', False)

        for rimName in rimProfiles.keys():
            self.rimInput.listItems.add(rimName, rimName == self.rim)
        
        # Set size dropdown to default rim selection on start, replace with others in HandleInputsChanged
        for size in rimProfiles[self.rimInput.selectedItem.name]['sizes'].keys():
            self.sizeInput.listItems.add(size, size == list(rimProfiles[self.rimInput.selectedItem.name]['sizes'].keys())[0])
            

        self.errorMessageTextInput = inputs.addTextBoxCommandInput('errMessage', '', '', 2, True)
        self.errorMessageTextInput.isFullWidth = True

        skipValidate = False

    def HandleInputsChanged(self, args: core.InputChangedEventArgs):
        changedInput = args.input
        
        if not skipValidate:
            if changedInput.id == 'rim':
                self.sizeInput.listItems.clear()
                rimSizes = rimProfiles[self.rimInput.selectedItem.name]['sizes'].keys()
                for size in rimSizes:
                    self.sizeInput.listItems.add(size, size == list(rimSizes)[0])

    def HandleValidateInputs(self, args: core.ValidateInputsEventArgs):
        pass

    def HandleExecute(self, args: core.CommandEventArgs):
        rimProfilePath = f'{self.resource_dir}{rimProfiles[self.rimInput.selectedItem.name]["profile"]}'
        spokeCount = int(self.spokesInput.selectedItem.name)
        createRim(rimProfilePath, self.rimInput.selectedItem.name, self.sizeInput.selectedItem.name, spokeCount)
    
def createRim(rimProfilePath: str, rim: str, size: float, spokeCount: int):
    schraederRadius = 0.4
    prestaRadius = 0.3
    spokeHoleRadius = 0.225
    nippleHoleRadius = 0.3

    importManager = app.importManager
    rootComp = design.rootComponent
    # Create a new component by creating an occurrence.
    occurence = rootComp.occurrences.addNewComponent(core.Matrix3D.create())
    newComp = occurence.component
    newComp.name = f'Rim {rim} x {size} x {spokeCount}'

    # Get dxf import options
    dxfOptions = importManager.createDXF2DImportOptions(rimProfilePath, newComp.xYConstructionPlane)
    dxfOptions.isViewFit = False

    # Set the flag true to merge all the layers of DXF into single sketch.
    dxfOptions.isSingleSketchResult = True

    # Import dxf file to root component
    importManager.importToTarget(dxfOptions, newComp)

    sketches = newComp.sketches

    # Get profile from imported sketch
    rimProfileSketch = sketches.item(0)
    rimProfile = rimProfileSketch.profiles.item(0)

    # Draw line to revolve around
    rimErd = rimProfiles[rim]['sizes'][size]
    revolveAxisSketch = fusion.Sketch.cast(sketches.add(newComp.xYConstructionPlane))
    revolveAxisSketch.name = 'Revolve Axis'
    lines = revolveAxisSketch.sketchCurves.sketchLines
    revolveAxis = lines.addByTwoPoints(createPoint(-1, rimErd / 2, 0), createPoint(1, rimErd / 2, 0))

    # Revolve rim profile around axis
    revolves = newComp.features.revolveFeatures
    revolveInput = revolves.createInput(rimProfile, revolveAxis, fusion.FeatureOperations.NewBodyFeatureOperation)
    revolveInput.setAngleExtent(False, core.ValueInput.createByReal(2 * pi))
    rimRevolve = revolves.add(revolveInput)

    # Mirror and join revolved body
    mirrors = newComp.features.mirrorFeatures
    collection = core.ObjectCollection.create()
    revolveBody = rimRevolve.bodies.item(0)
    collection.add(revolveBody)
    mirrorInput = mirrors.createInput(collection, newComp.yZConstructionPlane)
    mirrorInput.isCombine = True
    rimMirror = mirrors.add(mirrorInput)

    # Sketch valve hole profile
    valveHoleSketch = fusion.Sketch.cast(sketches.add(newComp.xYConstructionPlane))
    valveHoleSketch.name = 'Valve Hole'
    circles = valveHoleSketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(createPoint(0, rimErd / 2, 0), schraederRadius)
    valveHoleProfile = valveHoleSketch.profiles.item(0)

    # Cut valve hole in rim
    extrudes = newComp.features.extrudeFeatures
    extrudeInput = extrudes.createInput(valveHoleProfile, fusion.FeatureOperations.CutFeatureOperation)
    extentDef = fusion.ThroughAllExtentDefinition.create()
    extendDir = fusion.ExtentDirections.NegativeExtentDirection
    extrudeInput.setOneSideExtent(extentDef, extendDir)
    extrudes.add(extrudeInput)

    # Cut spoke holes in rim
    # Create angled plane for first extrude cut
    constructionPlanes = newComp.constructionPlanes
    spokeHolePlaneInput: fusion.ConstructionPlaneInput = constructionPlanes.createInput()
    spokeHolePlaneInput.setByAngle(revolveAxis, core.ValueInput.createByReal(2 * pi / spokeCount / 2), newComp.xYConstructionPlane)
    spokeHolePlane = constructionPlanes.add(spokeHolePlaneInput)

    # Create sketch for spoke hole cut
    spokeHoleSketch = fusion.Sketch.cast(sketches.add(spokeHolePlane))
    circles = spokeHoleSketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(createPoint(0, 0, 0), spokeHoleRadius)
    circles.addByCenterRadius(createPoint(0, 0, 0), nippleHoleRadius)
    spokeHoleProfile = spokeHoleSketch.profiles.item(0)
    nippleHoleProfile = spokeHoleSketch.profiles.item(1)

    # Extrude first spoke hole
    spokeHoleExtrudeInput = extrudes.createInput(spokeHoleProfile, fusion.FeatureOperations.CutFeatureOperation)
    extentDef = fusion.ThroughAllExtentDefinition.create()
    extentDir = fusion.ExtentDirections.NegativeExtentDirection
    spokeHoleExtrudeInput.setOneSideExtent(extentDef, extentDir)
    spokeHoleExtrudeFeature = extrudes.add(spokeHoleExtrudeInput)

    # Round pattern the spoke hole
    patterns = newComp.features.circularPatternFeatures
    collection = core.ObjectCollection.create()
    collection.add(spokeHoleExtrudeFeature)
    spokeHolePatternInput = patterns.createInput(collection, revolveAxis)
    spokeHolePatternInput.quantity = core.ValueInput.createByReal(spokeCount)
    spokeHolePatternInput.isSymmetric = False
    spokeHolePatternInput.totalAngle = core.ValueInput.createByReal(2 * pi)
    spokeHolePatternFeature = patterns.add(spokeHolePatternInput)

    # Enlarge spoke holes in outer rim wall
    nippleHoleExtrudeInput = extrudes.createInput(nippleHoleProfile, fusion.FeatureOperations.CutFeatureOperation)
    offsetStart: fusion.OffsetStartDefinition = fusion.OffsetStartDefinition.create(core.ValueInput.createByReal(rimErd / 2))
    extentDef = fusion.ThroughAllExtentDefinition.create()
    extentDir = fusion.ExtentDirections.NegativeExtentDirection
    nippleHoleExtrudeInput.startExtent = offsetStart
    nippleHoleExtrudeInput.setOneSideExtent(extentDef, extentDir)
    nippleHoleExtrudeFeature = extrudes.add(nippleHoleExtrudeInput)

    # Round pattern the nipple hole
    collection = core.ObjectCollection.create()
    collection.add(nippleHoleExtrudeFeature)
    nippleHolePatternInput = patterns.createInput(collection, revolveAxis)
    nippleHolePatternInput.quantity = core.ValueInput.createByReal(spokeCount)
    nippleHolePatternInput.isSymmetric = False
    nippleHolePatternInput.totalAngle = core.ValueInput.createByReal(2 * pi)
    nippleHolePatternFeature = patterns.add(nippleHolePatternInput)

    newComp.isSketchFolderLightBulbOn = False
    newComp.isConstructionFolderLightBulbOn = False