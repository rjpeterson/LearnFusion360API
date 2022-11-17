import os
from math import pi

import adsk.core as core
import adsk.fusion as fusion

app = core.Application.get()
if app:
    ui = app.userInterface
    createPoint = core.Point3D.create
    alert = ui.messageBox
design = fusion.Design.cast(app.activeProduct)
if not design:
    alert("You must be in the design workspace to use this command")
skipValidate = False

hubData = {}
_origin = createPoint(0, 0, 0)
_locknutToRotorFront = 0.99
_locknutToRotorRear = 1.45


class HubLogic:
    @property
    def resource_dir(self):
        try:
            _resource_dir = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "resources"
            )
            return _resource_dir if os.path.isdir(_resource_dir) else ""
        except:
            return ""

    def __init__(self) -> None:
        self.preset = "None"
        self.hubType = "Front"
        self.brakeType = "Rim"
        self.axleType = "QR"
        self.axleDia = 0.9
        self.old = 10.0
        self.leftFlangeDia = 6.2
        self.rightFlangeDia = 6.2
        self.centerToLeftFlange = 3.33
        self.centerToRightFlange = 3.33
        self.spokes = 32

    def CreateCommandInputs(self, inputs: core.CommandInputs):
        global skipValidate
        skipValidate = True

        self.presetInput = inputs.addDropDownCommandInput(
            "preset", "Preset", core.DropDownStyles.TextListDropDownStyle
        )
        self.presetInput.listItems.add("None", True)
        self.presetInput.listItems.add("Shimano Deore XT FH-M8110-B 148mm Rear", False)
        self.presetInput.listItems.add("White Industries Track Rear non-f/f", False)

        self.hubTypeInput = inputs.addRadioButtonGroupCommandInput(
            "hubType", "Hub Type"
        )
        self.frontOption: core.ListItem = self.hubTypeInput.listItems.add("Front", True)
        self.rearOption: core.ListItem = self.hubTypeInput.listItems.add("Rear", False)

        self.brakeTypeInput = inputs.addRadioButtonGroupCommandInput(
            "brakeType", "Brake Type"
        )
        self.rimOption: core.ListItem = self.brakeTypeInput.listItems.add("Rim", True)
        self.sixBoltOption: core.ListItem = self.brakeTypeInput.listItems.add(
            "Disc 6-bolt", False
        )
        self.centerLockOption: core.ListItem = self.brakeTypeInput.listItems.add(
            "Disc CenterLock", False
        )

        self.axleTypeInput = inputs.addRadioButtonGroupCommandInput(
            "axleType", "Axle Type"
        )
        self.qrOption: core.ListItem = self.axleTypeInput.listItems.add(
            "QR", True
        )  # Front 9mm Rear 10mm
        self.thruMTBOption: core.ListItem = self.axleTypeInput.listItems.add(
            "Thru MTB", False
        )  # Front 15mm Rear 12mm
        self.thruRoadOption: core.ListItem = self.axleTypeInput.listItems.add(
            "Thru Road", False
        )  # Front 12mm Rear 12mm
        self.solidOption: core.ListItem = self.axleTypeInput.listItems.add(
            "Solid", False
        )

        self.oldInput = inputs.addValueInput(
            "old",
            "Over Locknut Distance",
            "mm",
            core.ValueInput.createByString("100 mm"),
        )
        self.leftFlangeDiaInput = inputs.addValueInput(
            "leftFlangeDia",
            "Left Flange Diameter",
            "mm",
            core.ValueInput.createByString("62 mm"),
        )
        self.rightFlangeDiaInput = inputs.addValueInput(
            "rightFlangeDia",
            "Right Flange Diameter",
            "mm",
            core.ValueInput.createByString("62 mm"),
        )
        self.centerToLeftFlangeInput = inputs.addValueInput(
            "centerToLeftFlange",
            "Center to Left Flange",
            "mm",
            core.ValueInput.createByString("33.3 mm"),
        )
        self.centerToRightFlangeInput = inputs.addValueInput(
            "centerToRightFlange",
            "Center to Right Flange",
            "mm",
            core.ValueInput.createByString("33.3 mm"),
        )
        self.spokesInput = inputs.addIntegerSpinnerCommandInput(
            "spokes", "Spokes", 2, 48, 2, 32
        )

        self.errorMessageTextInput = inputs.addTextBoxCommandInput(
            "errMessage", "", "", 2, True
        )
        self.errorMessageTextInput.isFullWidth = True

        skipValidate = False

    def HandleInputsChanged(self, args: core.InputChangedEventArgs):
        changedInput = args.input
        if not skipValidate:
            if changedInput.id == "preset":
                if (
                    self.presetInput.selectedItem.name
                    == "Shimano Deore XT FH-M8110-B 148mm Rear"
                ):
                    self.rearOption.isSelected = True
                    self.centerLockOption.isSelected = True
                    self.thruMTBOption.isSelected = True
                    self.oldInput.value = 14.8
                    self.leftFlangeDiaInput.value = 6.0
                    self.rightFlangeDiaInput.value = 6.1
                    self.centerToLeftFlangeInput.value = 3.6
                    self.centerToRightFlangeInput.value = 2.2
                if (
                    self.presetInput.selectedItem.name
                    == "White Industries Track Rear non-f/f"
                ):
                    self.rearOption.isSelected = True
                    self.rimOption.isSelected = True
                    self.solidOption.isSelected = True
                    self.oldInput.value = 12.0
                    self.leftFlangeDiaInput.value = 7.3
                    self.rightFlangeDiaInput.value = 7.3
                    self.centerToLeftFlangeInput.value = 3.55
                    self.centerToRightFlangeInput.value = 3.0
            elif changedInput.id == "hubType" or changedInput.id == "axleType":
                if self.hubTypeInput == "Front":
                    if self.axleTypeInput == "QR":
                        self.axleDia = 0.9
                    elif self.axleTypeInput == "Thru MTB":
                        self.axleDia = 1.5
                    elif self.axleTypeInput == "Thru Road":
                        self.axleDia = 1.2
                    else:  # "Solid"
                        self.axleDia = 0.9
                else:  # "Rear"
                    if self.axleTypeInput == "QR" or self.axleTypeInput == "Solid":
                        self.axleDia = 1.0
                    else:  # "Thru"
                        self.axleDia = 1.2

    def HandleValidateInputs(self, args: core.ValidateInputsEventArgs):
        self.errorMessageTextInput.text = ""
        if not skipValidate:
            args.areInputsValid = False
            if self.oldInput.value <= 0:
                self.errorMessageTextInput.text = "OLD must be greater than 0"
            elif (
                self.leftFlangeDiaInput.value <= 0
                or self.rightFlangeDiaInput.value <= 0
            ):
                self.errorMessageTextInput.text = (
                    "Flange Diameters must be greater than 0"
                )
            elif self.centerToLeftFlangeInput.value <= 0:
                self.errorMessageTextInput.text = (
                    "Center to Left Flange must be greater than 0"
                )
            elif self.centerToRightFlangeInput.value <= 0:
                self.errorMessageTextInput.text = (
                    "Center to Right Flange must be greater than 0"
                )
            elif (
                self.centerToLeftFlangeInput.value + self.centerToRightFlangeInput.value
                > self.oldInput.value
            ):
                self.errorMessageTextInput.text = (
                    "Sum of left and right flange distances cannot be larger than OLD"
                )
            elif (
                self.leftFlangeDiaInput.value <= self.axleDia + 2.5
                or self.rightFlangeDiaInput.value <= self.axleDia + 2.5
            ):
                self.errorMessageTextInput.text = (
                    "One or both Flange Diameters is too small"
                )
            else:
                args.areInputsValid = True

    def HandleExecute(self, args: core.CommandEventArgs):
        self.preset = self.presetInput.selectedItem.name
        self.old = self.oldInput.value
        self.spokes = self.spokesInput.value
        self.brakeType = self.brakeTypeInput.selectedItem.name
        self.hubType = self.hubTypeInput.selectedItem.name
        self.axleType = self.axleTypeInput.selectedItem.name
        self.leftFlangeDia = self.leftFlangeDiaInput.value
        self.rightFlangeDia = self.rightFlangeDiaInput.value
        self.centerToLeftFlange = self.centerToLeftFlangeInput.value
        self.centerToRightFlange = self.centerToRightFlangeInput.value
        createHub(self)


def createHub(logic: HubLogic):
    leftFlangeRad = logic.leftFlangeDia / 2
    rightFlangeRad = logic.rightFlangeDia / 2
    axleRad = logic.axleDia / 2
    if logic.axleType == "Solid":
        axleExtent = logic.old + 3
    else:
        axleExtent = logic.old + 0.4

    # importManager = app.importManager
    rootComp = design.rootComponent
    # Create a new component by creating an occurrence.
    occurence = rootComp.occurrences.addNewComponent(core.Matrix3D.create())
    newComp = occurence.component
    if logic.preset != "None":
        newComp.name = logic.preset
    else:
        newComp.name = f"{logic.hubType} {logic.axleType} {logic.old}  x {logic.spokes}"

    sketches = newComp.sketches

    # sketch axle
    axleSketch = fusion.Sketch.cast(sketches.add(newComp.yZConstructionPlane))
    circles = axleSketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(_origin, axleRad)
    circles.addByCenterRadius(_origin, axleRad - 0.2)

    # extrude axle
    extrudes = newComp.features.extrudeFeatures
    collection = core.ObjectCollection.create()
    for profile in axleSketch.profiles:
        if logic.axleType == "Solid":
            collection.add(profile)
        elif profile.profileLoops.count == 2:
            collection.add(profile)
    axleExtrudeInput = extrudes.createInput(
        collection, fusion.FeatureOperations.NewBodyFeatureOperation
    )
    axleExtrudeInput.setSymmetricExtent(core.ValueInput.createByReal(axleExtent), True)
    axleExtrude = extrudes.add(axleExtrudeInput)
    axleExtrude.bodies.item(0).name = "Axle"

    # sketch flanges
    leftFlangeSketch = fusion.Sketch.cast(sketches.add(newComp.yZConstructionPlane))
    circles = leftFlangeSketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(_origin, leftFlangeRad + 0.3)
    leftFlangeProfile = leftFlangeSketch.profiles.item(0)
    rightFlangeSketch = fusion.Sketch.cast(sketches.add(newComp.yZConstructionPlane))
    circles = rightFlangeSketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(_origin, rightFlangeRad + 0.3)
    rightFlangeProfile = rightFlangeSketch.profiles.item(0)

    # API doesnt support sketch patterns, so we have to extrude flanges first, extrude a spoke hole, and then pattern the feature
    # extrude flanges
    lFlangeExtrudeInput = extrudes.createInput(
        leftFlangeProfile, fusion.FeatureOperations.NewBodyFeatureOperation
    )
    offsetStart: fusion.OffsetStartDefinition = fusion.OffsetStartDefinition.create(
        core.ValueInput.createByReal(-logic.centerToLeftFlange + 0.1)
    )
    extentDef: fusion.DistanceExtentDefinition = fusion.DistanceExtentDefinition.create(
        core.ValueInput.createByReal(0.2)
    )
    extentDir = fusion.ExtentDirections.NegativeExtentDirection
    lFlangeExtrudeInput.startExtent = offsetStart
    lFlangeExtrudeInput.setOneSideExtent(extentDef, extentDir)
    lFlangeExtrude = extrudes.add(lFlangeExtrudeInput)
    lFlangeBody = lFlangeExtrude.bodies.item(0)
    lFlangeBody.name = "Left Flange"

    rFlangeExtrudeInput = extrudes.createInput(
        rightFlangeProfile, fusion.FeatureOperations.NewBodyFeatureOperation
    )
    offsetStart: fusion.OffsetStartDefinition = fusion.OffsetStartDefinition.create(
        core.ValueInput.createByReal(logic.centerToRightFlange - 0.1)
    )
    extentDef: fusion.DistanceExtentDefinition = fusion.DistanceExtentDefinition.create(
        core.ValueInput.createByReal(0.2)
    )
    extentDir = fusion.ExtentDirections.PositiveExtentDirection
    rFlangeExtrudeInput.startExtent = offsetStart
    rFlangeExtrudeInput.setOneSideExtent(extentDef, extentDir)
    rFlangeExtrude = extrudes.add(rFlangeExtrudeInput)
    rFlangeBody = rFlangeExtrude.bodies.item(0)
    rFlangeBody.name = "Right Flange"

    # cut single spoke hole TODO add left and right difference flange diameters
    leftSpokeHoleSketch = fusion.Sketch.cast(sketches.add(newComp.yZConstructionPlane))
    circles = leftSpokeHoleSketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(createPoint(0, leftFlangeRad, 0), 0.125)
    leftSpokeHoleProfile = leftSpokeHoleSketch.profiles.item(0)
    leftSpokeHoleExtrudeInput = extrudes.createInput(
        leftSpokeHoleProfile, fusion.FeatureOperations.CutFeatureOperation
    )
    extent = fusion.DistanceExtentDefinition.create(
        core.ValueInput.createByReal(logic.centerToLeftFlange + 1)
    )
    leftSpokeHoleExtrudeInput.setOneSideExtent(
        extent, fusion.ExtentDirections.NegativeExtentDirection
    )
    leftSpokeHoleCut = extrudes.add(leftSpokeHoleExtrudeInput)

    rightSpokeHoleSketch = fusion.Sketch.cast(sketches.add(newComp.yZConstructionPlane))
    circles = rightSpokeHoleSketch.sketchCurves.sketchCircles
    circles.addByCenterRadius(createPoint(0, rightFlangeRad, 0), 0.125)
    rightSpokeHoleProfile = rightSpokeHoleSketch.profiles.item(0)
    rightSpokeHoleExtrudeInput = extrudes.createInput(
        rightSpokeHoleProfile, fusion.FeatureOperations.CutFeatureOperation
    )
    extent = fusion.DistanceExtentDefinition.create(
        core.ValueInput.createByReal(logic.centerToRightFlange + 1)
    )
    rightSpokeHoleExtrudeInput.setOneSideExtent(
        extent, fusion.ExtentDirections.PositiveExtentDirection
    )
    rightSpokeHoleCut = extrudes.add(rightSpokeHoleExtrudeInput)

    # circular pattern spoke hole
    # TODO figure out why this breaks every other run
    patterns = newComp.features.circularPatternFeatures
    collection = core.ObjectCollection.create()
    collection.add(leftSpokeHoleCut)
    collection.add(rightSpokeHoleCut)
    spokeHolePatternInput = patterns.createInput(collection, newComp.xConstructionAxis)
    spokeHolePatternInput.isSymmetric = False
    spokeHolePatternInput.quantity = core.ValueInput.createByReal(logic.spokes / 2)
    spokeHolePatternInput.totalAngle = core.ValueInput.createByReal(2 * pi)
    spokeHolePattern = patterns.add(spokeHolePatternInput)

    # offest one flange body
    moves = newComp.features.moveFeatures
    collection = core.ObjectCollection.create()
    collection.add(rFlangeBody)
    transform = core.Matrix3D.create()
    transform.setToRotation(
        (2 * pi) / logic.spokes,
        newComp.xConstructionAxis.geometry.direction,
        _origin,
    )
    flangeRotateInput = moves.createInput(collection, transform)
    moves.add(flangeRotateInput)

    # sketch axle hardware
    axleHardwareSketch = fusion.Sketch.cast(sketches.add(newComp.xZConstructionPlane))
    lines = axleHardwareSketch.sketchCurves.sketchLines
    hardwareRad = 0.75
    lines.addTwoPointRectangle(
        createPoint(-logic.old / 2, axleRad + 0.05, 0),
        createPoint(logic.old / 2, hardwareRad, 0),
    )
    axleHardwareProfile = axleHardwareSketch.profiles.item(0)

    # revolve axle hardware
    revolves = newComp.features.revolveFeatures
    hardwareRevolveInput = revolves.createInput(
        axleHardwareProfile,
        newComp.xConstructionAxis,
        fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    hardwareRevolveInput.setAngleExtent(False, core.ValueInput.createByReal(2 * pi))
    axleHardwareRevolve = revolves.add(hardwareRevolveInput)
    axleHardwareRevolve.bodies.item(0).name = "Axle Hardware"

    # Mirror and join revolved body
    # mirrors = newComp.features.mirrorFeatures
    # collection = core.ObjectCollection.create()
    # revolveBody = rimRevolve.bodies.item(0)
    # collection.add(revolveBody)
    # mirrorInput = mirrors.createInput(collection, newComp.yZConstructionPlane)
    # mirrorInput.isCombine = True
    # rimMirror = mirrors.add(mirrorInput)

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