import os
from math import pi
from enum import Enum

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

class HubType(Enum):
    Front = 1
    Rear = 2

class BrakeType(Enum):
    Rim = 1
    Sixbolt = 2
    CenterLock = 3

class AxleType(Enum):
    Solid = 1
    QR = 2
    ThruRoad = 3
    ThruMTB = 4

hubData = {
    "Chris King R45D CL Front": {
        "type": HubType.Front,
        "brake": BrakeType.CenterLock,
        "axle": AxleType.ThruRoad,
        "old": 10.0,
        "leftFlangeDia": 5.74,
        "rightFlangeDia": 5.74,
        "centerToLeftFlange": 2.23,
        "centerToRightFlange": 3.06,
    },
    "Chris King R45D CL Rear": {
        "type": HubType.Rear,
        "brake": BrakeType.CenterLock,
        "axle": AxleType.ThruRoad,
        "old": 14.2,
        "leftFlangeDia": 5.74,
        "rightFlangeDia": 5.74,
        "centerToLeftFlange": 3.3,
        "centerToRightFlange": 1.87,
    },
    "Hope Pro 4 Boost Front": {
        "type": HubType.Front,
        "brake": BrakeType.Sixbolt,
        "axle": AxleType.ThruMTB,
        "old": 11.0,
        "leftFlangeDia": 5.7,
        "rightFlangeDia": 5.7,
        "centerToLeftFlange": 2.5,
        "centerToRightFlange": 3.3,
    },
    "Hope Pro 4 Boost Rear": {
        "type": HubType.Rear,
        "brake": BrakeType.Sixbolt,
        "axle": AxleType.ThruMTB,
        "old": 14.8,
        "leftFlangeDia": 5.7,
        "rightFlangeDia": 5.7,
        "centerToLeftFlange": 3.5,
        "centerToRightFlange": 2.2,
    },
    "Phil Wood CL Shimano Compatible Front": {
        "type": HubType.Front,
        "brake": BrakeType.CenterLock,
        "axle": AxleType.QR,
        "old": 10.0,
        "leftFlangeDia": 6.6,
        "rightFlangeDia": 6.6,
        "centerToLeftFlange": 1.9,
        "centerToRightFlange": 3.4,
    },
    "Phil Wood CL Shimano Compatible Rear": {
        "type": HubType.Rear,
        "brake": BrakeType.CenterLock,
        "axle": AxleType.QR,
        "old": 13.5,
        "leftFlangeDia": 6.6,
        "rightFlangeDia": 6.6,
        "centerToLeftFlange": 3.5,
        "centerToRightFlange": 1.8,
    },
    "White Industries Track Front": {
        "type": HubType.Front,
        "brake": BrakeType.Rim,
        "axle": AxleType.Solid,
        "old": 10.0,
        "leftFlangeDia": 6.5,
        "rightFlangeDia": 6.5,
        "centerToLeftFlange": 3.3,
        "centerToRightFlange": 3.3,
    },
    "White Industries Track Rear non-f/f": {
        "type": HubType.Rear,
        "brake": BrakeType.Rim,
        "axle": AxleType.Solid,
        "old": 12.0,
        "leftFlangeDia": 7.3,
        "rightFlangeDia": 7.3,
        "centerToLeftFlange": 3.55,
        "centerToRightFlange": 3.0,
    }
}
_origin = createPoint(0, 0, 0)
_locknutToRotorFront = 0.99
_locknutToRotorRear = 1.45

axleDiameters = {
    "Front": {
        "QR" : 0.9,
        "ThruMTB": 1.5,
        "ThruRoad": 1.2,
        "Solid": 0.9
    },
    "Rear": {
        "QR": 1.0,
        "ThruMTB": 1.2,
        "ThruRoad": 1.2,
        "Solid": 1.0
    }
}

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
        for hub in hubData:
            self.presetInput.listItems.add(hub, False)

        self.hubTypeInput = inputs.addRadioButtonGroupCommandInput(
            "hubType", "Hub Type"
        )
        self.frontOption: core.ListItem = self.hubTypeInput.listItems.add("Front", True)
        self.rearOption: core.ListItem = self.hubTypeInput.listItems.add("Rear", False)

        self.brakeTypeInput = inputs.addRadioButtonGroupCommandInput(
            "brakeType", "Brake Type"
        )
        self.brakeRimOption: core.ListItem = self.brakeTypeInput.listItems.add("Rim", True)
        self.brakeSixBoltOption: core.ListItem = self.brakeTypeInput.listItems.add(
            "Sixbolt", False
        )
        self.brakeCenterLockOption: core.ListItem = self.brakeTypeInput.listItems.add(
            "Disc CenterLock", False
        )

        self.axleTypeInput = inputs.addRadioButtonGroupCommandInput(
            "axleType", "Axle Type"
        )
        self.axleQrOption: core.ListItem = self.axleTypeInput.listItems.add(
            "QR", True
        )  # Front 9mm Rear 10mm
        self.axleThruMTBOption: core.ListItem = self.axleTypeInput.listItems.add(
            "ThruMTB", False
        )  # Front 15mm Rear 12mm
        self.axleThruRoadOption: core.ListItem = self.axleTypeInput.listItems.add(
            "ThruRoad", False
        )  # Front 12mm Rear 12mm
        self.axleSolidOption: core.ListItem = self.axleTypeInput.listItems.add(
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
                if self.presetInput.selectedItem.name != "None":
                    chosenHub = hubData[self.presetInput.selectedItem.name]
                    hubType: HubType = chosenHub["type"]
                    brakeType: BrakeType = chosenHub["brake"]
                    axleType: AxleType = chosenHub["axle"]
                    if hubType == HubType.Front:
                        self.frontOption.isSelected = True
                    else:
                        self.rearOption.isSelected = True

                    if brakeType == BrakeType.Rim:
                        self.brakeRimOption.isSelected = True
                    elif brakeType == BrakeType.Sixbolt:
                        self.brakeSixBoltOption.isSelected = True
                    else: # BrakeType.CL
                        self.brakeCenterLockOption.isSelected = True

                    if axleType == AxleType.Solid:
                        self.axleSolidOption.isSelected = True
                    elif axleType == AxleType.QR:
                        self.axleQrOption.isSelected = True
                    elif axleType == AxleType.ThruMTB:
                        self.axleThruMTBOption.isSelected = True
                    else: # AxleType.THRUROAD
                        self.axleThruRoadOption.isSelected = True

                    self.oldInput.value = chosenHub["old"]
                    self.leftFlangeDiaInput.value = chosenHub["leftFlangeDia"]
                    self.rightFlangeDiaInput.value = chosenHub["rightFlangeDia"]
                    self.centerToLeftFlangeInput.value = chosenHub["centerToLeftFlange"]
                    self.centerToRightFlangeInput.value = chosenHub["centerToRightFlange"]
                # if (
                #     self.presetInput.selectedItem.name
                #     == "Shimano Deore XT FH-M8110-B 148mm Rear"
                # ):
                #     self.rearOption.isSelected = True
                #     self.brakeCenterLockOption.isSelected = True
                #     self.axleThruMTBOption.isSelected = True
                #     self.oldInput.value = 14.8
                #     self.leftFlangeDiaInput.value = 6.0
                #     self.rightFlangeDiaInput.value = 6.1
                #     self.centerToLeftFlangeInput.value = 3.6
                #     self.centerToRightFlangeInput.value = 2.2
                # if (
                #     self.presetInput.selectedItem.name
                #     == "White Industries Track Rear non-f/f"
                # ):
                #     self.rearOption.isSelected = True
                #     self.brakeRimOption.isSelected = True
                #     self.axleSolidOption.isSelected = True
                #     self.oldInput.value = 12.0
                #     self.leftFlangeDiaInput.value = 7.3
                #     self.rightFlangeDiaInput.value = 7.3
                #     self.centerToLeftFlangeInput.value = 3.55
                #     self.centerToRightFlangeInput.value = 3.0
            elif changedInput.id == "hubType" or changedInput.id == "axleType":
                self.axleDia = axleDiameters[self.hubTypeInput.selectedItem.name][self.axleTypeInput.selectedItem.name]

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

    importManager = app.importManager
    
    rootComp = design.rootComponent
    # Create a new component by creating an occurrence.
    occurence = rootComp.occurrences.addNewComponent(core.Matrix3D.create())
    newComp = occurence.component
    if logic.preset != "None":
        newComp.name = logic.preset
    else:
        newComp.name = f"{logic.hubType} {logic.axleType} {logic.old}  x {logic.spokes}"

    sketches = newComp.sketches

    # Get dxf import options
    freehubBaseOptions = importManager.createDXF2DImportOptions(f'{logic.resource_dir}/freehub_base.dxf', newComp.yZConstructionPlane)
    freehubBaseOptions.isViewFit = False
    freehubSplinesOptions = importManager.createDXF2DImportOptions(f'{logic.resource_dir}/freehub_splines.dxf', newComp.yZConstructionPlane)
    freehubSplinesOptions.isViewFit = False
    sixBoltBossOptions = importManager.createDXF2DImportOptions(f'{logic.resource_dir}/six_bolt_boss.dxf', newComp.yZConstructionPlane)
    sixBoltBossOptions.isViewFit = False
    centerlockBossOptions = importManager.createDXF2DImportOptions(f'{logic.resource_dir}/centerlock_boss.dxf', newComp.yZConstructionPlane)
    centerlockBossOptions.isViewFit = False
    centerlockSplinesOptions = importManager.createDXF2DImportOptions(f'{logic.resource_dir}/centerlock_splines.dxf', newComp.yZConstructionPlane)
    centerlockSplinesOptions.isViewFit = False


    # Set the flag true to merge all the layers of DXF into single sketch.
    freehubBaseOptions.isSingleSketchResult = True
    freehubSplinesOptions.isSingleSketchResult = True
    sixBoltBossOptions.isSingleSketchResult = True
    centerlockBossOptions.isSingleSketchResult = True
    centerlockSplinesOptions.isSingleSketchResult = True

    # Import dxf file to root component
    importManager.importToTarget(freehubBaseOptions, newComp)
    importManager.importToTarget(freehubSplinesOptions, newComp)
    importManager.importToTarget(sixBoltBossOptions, newComp)
    importManager.importToTarget(centerlockBossOptions, newComp)
    importManager.importToTarget(centerlockSplinesOptions, newComp)

    freehubBaseSketch = sketches.itemByName('freehub_base')
    freehubSplinesSketch = sketches.itemByName('freehub_splines')
    sixBoltBossSketch = sketches.itemByName('six_bolt_boss')
    centerlockBossSketch = sketches.itemByName('centerlock_boss')
    centerlockSplinesSketch = sketches.itemByName('centerlock_splines')

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
    lFlangeBodyOutsideFaceEdges = lFlangeExtrude.endFaces.item(0).edges

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
    rFlangeBodyOutsideFaceEdges = rFlangeExtrude.endFaces.item(0).edges

    # cut single spoke hole
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
    spokeHolePatternInput.patternComputeOption = fusion.PatternComputeOptions.OptimizedPatternCompute
    spokeHolePattern = patterns.add(spokeHolePatternInput)

    # get edges for wheel assembly
    lSpokeHoleEdges = []
    rSpokeHoleEdges = []
    lSpokeHoleEdges.append(leftSpokeHoleCut.sideFaces.item(0).edges.item(0))
    rSpokeHoleEdges.append(rightSpokeHoleCut.sideFaces.item(0).edges.item(0))
    for face in spokeHolePattern.faces:
        for edge in face.edges:
            if edge in lFlangeBodyOutsideFaceEdges:
                lSpokeHoleEdges.append(edge)
            elif edge in rFlangeBodyOutsideFaceEdges:
                rSpokeHoleEdges.append(edge)

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

    # sketch hub body
    hubBodySketch = fusion.Sketch.cast(sketches.add(newComp.xZConstructionPlane))
    lines = hubBodySketch.sketchCurves.sketchLines
    leftBodyRad = (leftFlangeRad + hardwareRad) / 2.5
    rightBodyRad = (rightFlangeRad + hardwareRad) / 2.5
    point1 = createPoint((-logic.old / 2) + 0.5, 0, 0)
    point2 = createPoint((-logic.old / 2) + 0.5, leftBodyRad, 0)
    point3 = createPoint(-logic.centerToLeftFlange, leftBodyRad, 0)
    point4 = createPoint(logic.centerToRightFlange, rightBodyRad, 0)
    if logic.hubType == "Front":
        point5 = createPoint((logic.old / 2) - 0.5, leftBodyRad, 0)
        point6 = createPoint((logic.old / 2) - 0.5, 0, 0)
    else:
        point5 = createPoint(logic.centerToRightFlange + 0.2, rightBodyRad, 0)
        point6 = createPoint(logic.centerToRightFlange + 0.2, 0, 0)
    lines.addByTwoPoints(point1, point2)
    lines.addByTwoPoints(point2, point3)
    lines.addByTwoPoints(point3, point4)
    lines.addByTwoPoints(point4, point5)
    lines.addByTwoPoints(point5, point6)
    lines.addByTwoPoints(point6, point1)
    #
    bodyProfile = hubBodySketch.profiles.item(0)

    # revolve hub body
    bodyRevolveInput = revolves.createInput(
        bodyProfile,
        newComp.xConstructionAxis,
        fusion.FeatureOperations.NewBodyFeatureOperation,
    )
    bodyRevolveInput.setAngleExtent(False, core.ValueInput.createByReal(2 * pi))
    bodyRevolve = revolves.add(bodyRevolveInput)
    bodyRevolve.bodies.item(0).name = "Hub Body"

    # if rear
    if logic.hubType == "Rear":
        # sketch freehub
        freehubSketch = fusion.Sketch.cast(sketches.add(newComp.xZConstructionPlane))
        lines = freehubSketch.sketchCurves.sketchLines
        freehubRad = 1.7
        freehubStart = logic.centerToRightFlange + 0.2
        freehubEnd = (logic.old / 2) - 1
        lines.addTwoPointRectangle(
            createPoint(freehubStart, hardwareRad + 0.3, 0),
            createPoint(freehubEnd, freehubRad, 0),
        )
        freehubProfile = freehubSketch.profiles.item(0)



        # extrude freehub Base
        collection = core.ObjectCollection.create()
        collection.add(freehubBaseSketch.profiles.item(0))
        collection.add(freehubBaseSketch.profiles.item(1))
        freehubBaseExtrudeInput = extrudes.createInput(collection, fusion.FeatureOperations.NewBodyFeatureOperation)
        offsetStart: fusion.OffsetStartDefinition = fusion.OffsetStartDefinition.create(
            core.ValueInput.createByReal(logic.centerToRightFlange)
        )
        extent = .5
        extentDef: fusion.DistanceExtentDefinition = (
            fusion.DistanceExtentDefinition.create(core.ValueInput.createByReal(extent))
        )
        extentDir = fusion.ExtentDirections.PositiveExtentDirection
        freehubBaseExtrudeInput.startExtent = offsetStart
        freehubBaseExtrudeInput.setOneSideExtent(extentDef, extentDir)
        freehubBaseExtrude = extrudes.add(freehubBaseExtrudeInput)
        freehubBaseBody = freehubBaseExtrude.bodies.item(0)
        freehubBaseBody.name = "Freehub Base"

        # extrude freehub splines
        collection = core.ObjectCollection.create()
        # collection.add(freehubSplinesSketch.profiles.item(0))
        collection.add(freehubSplinesSketch.profiles.item(1))
        freehubSplinesExtrudeInput = extrudes.createInput(collection, fusion.FeatureOperations.NewBodyFeatureOperation)
        offsetStart: fusion.OffsetStartDefinition = fusion.OffsetStartDefinition.create(
            core.ValueInput.createByReal(logic.centerToRightFlange)
        )
        extent = (logic.old / 2) - logic.centerToRightFlange - 1
        extentDef: fusion.DistanceExtentDefinition = (
            fusion.DistanceExtentDefinition.create(core.ValueInput.createByReal(extent))
        )
        extentDir = fusion.ExtentDirections.PositiveExtentDirection
        freehubSplinesExtrudeInput.startExtent = offsetStart
        freehubSplinesExtrudeInput.setOneSideExtent(extentDef, extentDir)
        freehubSplinesExtrude = extrudes.add(freehubSplinesExtrudeInput)
        freehubSplinesBody = freehubSplinesExtrude.bodies.item(0)
        freehubSplinesBody.name = "Freehub Splines"

    if logic.brakeType == "Sixbolt": 
        # sketch boss circle
        for profile in sixBoltBossSketch.profiles:
            if profile.profileLoops.count > 2:
                bossProfile = profile
                break

        # extrude boss
        bossExtrudeInput = extrudes.createInput(
            bossProfile, fusion.FeatureOperations.NewBodyFeatureOperation
        )
        offsetStart: fusion.OffsetStartDefinition = fusion.OffsetStartDefinition.create(
            core.ValueInput.createByReal(-logic.centerToLeftFlange)
        )
        if logic.hubType == "Rear":
            extent = (logic.old / 2) - logic.centerToLeftFlange - _locknutToRotorRear
        else:
            extent = (logic.old / 2) - logic.centerToLeftFlange - _locknutToRotorFront
        extentDef: fusion.DistanceExtentDefinition = (
            fusion.DistanceExtentDefinition.create(core.ValueInput.createByReal(extent))
        )
        extentDir = fusion.ExtentDirections.NegativeExtentDirection
        bossExtrudeInput.startExtent = offsetStart
        bossExtrudeInput.setOneSideExtent(extentDef, extentDir)
        bossExtrude = extrudes.add(bossExtrudeInput)
        bossBody = bossExtrude.bodies.item(0)
        bossBody.name = "Rotor Boss"

    if logic.brakeType == "Disc CenterLock":  
        # sketch boss circle
        for profile in centerlockSplinesSketch.profiles:
            if profile.profileLoops.count > 1:
                bossProfile = profile
                break

        # extrude boss
        bossExtrudeInput = extrudes.createInput(
            bossProfile, fusion.FeatureOperations.NewBodyFeatureOperation
        )
        offsetStart: fusion.OffsetStartDefinition = fusion.OffsetStartDefinition.create(
            core.ValueInput.createByReal(-logic.centerToLeftFlange)
        )
        if logic.hubType == "Rear":
            extent = (logic.old / 2) - logic.centerToLeftFlange - _locknutToRotorRear
        else:
            extent = (logic.old / 2) - logic.centerToLeftFlange - _locknutToRotorFront
        extentDef: fusion.DistanceExtentDefinition = (
            fusion.DistanceExtentDefinition.create(core.ValueInput.createByReal(extent))
        )
        extentDir = fusion.ExtentDirections.NegativeExtentDirection
        bossExtrudeInput.startExtent = offsetStart
        bossExtrudeInput.setOneSideExtent(extentDef, extentDir)
        bossExtrude = extrudes.add(bossExtrudeInput)
        bossBody = bossExtrude.bodies.item(0)
        bossBody.name = "Rotor Splines"

        # sketch boss circle
        for profile in centerlockBossSketch.profiles:
            if profile.profileLoops.count > 1:
                bossProfile = profile
                break

        # extrude boss
        bossExtrudeInput = extrudes.createInput(
            bossProfile, fusion.FeatureOperations.NewBodyFeatureOperation
        )
        offsetStart: fusion.OffsetStartDefinition = fusion.OffsetStartDefinition.create(
            core.ValueInput.createByReal(-logic.centerToLeftFlange)
        )
        
        extent = .5
        extentDef: fusion.DistanceExtentDefinition = (
            fusion.DistanceExtentDefinition.create(core.ValueInput.createByReal(extent))
        )
        extentDir = fusion.ExtentDirections.NegativeExtentDirection
        bossExtrudeInput.startExtent = offsetStart
        bossExtrudeInput.setOneSideExtent(extentDef, extentDir)
        bossExtrude = extrudes.add(bossExtrudeInput)
        bossBody = bossExtrude.bodies.item(0)
        bossBody.name = "Rotor Boss"
        
    # chamfers & fillets
    newComp.isSketchFolderLightBulbOn = False
    
    # return edges to use for spoke joints
    return [lSpokeHoleEdges, rSpokeHoleEdges]
