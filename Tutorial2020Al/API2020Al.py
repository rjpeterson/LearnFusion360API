# Author-
# Description-

from ctypes import Union
import adsk.core as core
import adsk.fusion as fusion
import adsk.cam
import traceback


def run(context):
    ui = None

    try:
        app = core.Application.get()
        design: fusion.Design = app.activeProduct

        ui = app.userInterface
        rootComp = design.rootComponent

        createPoint = core.Point3D.create
        
        if app.activeEditObject.objectType != fusion.Sketch.classType():
            ui.messageBox('A sketch must be active')
            return

        sketch: fusion.Sketch = app.activeEditObject
        sketchLines = sketch.sketchCurves.sketchLines
        sketchArcs = sketch.sketchCurves.sketchArcs
        sketchCircles = sketch.sketchCurves.sketchCircles

        def drawProfile(quadrant: int):
            if quadrant == 1:
                modifiers = [1.0,1.0]
            elif quadrant == 2:
                modifiers = [-1.0,1.0]
            elif quadrant == 3:
                modifiers = [-1.0,-1.0]
            else:
                modifiers = [1.0,-1.0]

            points = [
                [0, .31],
                [.225, .31],
                [.55, .635],
                [.55, .85],
                [.31, .85],
                [.31, 1.0],
                [.85, 1.0]
            ]

            for i in range(len(points) - 1):
                sketchLines.addByTwoPoints(
                    createPoint(
                        points[i][0] * modifiers[0],
                        points[i][1] * modifiers[1],
                        0
                    ), createPoint(
                        points[i+1][0] * modifiers[0],
                        points[i+1][1] * modifiers[1],
                        0
                    ))

            arcStart = createPoint(
                points[len(points)-1][0] * modifiers[0],
                points[len(points)-1][1] * modifiers[1]
            )
            arcCenter = createPoint(.85 * modifiers[0], .85 * modifiers[1], 0)
            sketchArcs.addByCenterStartSweep(arcCenter, arcStart, -1.5708 * modifiers[0] * modifiers[1])
            for i in range(len(points) - 1):
                sketchLines.addByTwoPoints(
                    createPoint(
                        points[i][1] * modifiers[0],
                        points[i][0] * modifiers[1],
                        0
                    ), createPoint(
                        points[i+1][1] * modifiers[0], 
                        points[i+1][0] * modifiers[1], 
                        0
                    ))
        
        for i in range(1,5):
            drawProfile(i)

        sketchCircles.addByCenterRadius(createPoint(0,0,0), .25)
        profile = rootComp.sketches.item(0).profiles.item(0)
        # if design.activateRootComponent():
        input = rootComp.features.extrudeFeatures.createInput(profile, fusion.FeatureOperations.NewBodyFeatureOperation)
        extent = fusion.DistanceExtentDefinition.create(core.ValueInput.createByReal(50))
        input.setOneSideExtent(extent, fusion.ExtentDirections.PositiveExtentDirection)
        rootComp.features.extrudeFeatures.add(input)
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


