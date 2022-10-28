#Author-
#Description-

import adsk.core as core, adsk.fusion as fusion, adsk.cam, traceback

directions = {
    'XPOS': '0',
    'XNEG': '1',
    'YPOS': '2',
    'YNEG': '3',
    'ZPOS': '4',
    'ZNEG': '5'
}

inverseDirections = {
    'XPOS': 'XNEG',
    'XNEG': 'XPOS',
    'YPOS': 'YNEG',
    'YNEG': 'YPOS',
    'ZPOS': 'ZNEG',
    'ZNEG': 'ZPOS'
}

def base(decimal ,base) :
    list = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    answer = ""
    while decimal != 0 :
        answer  += list[decimal % base]
        decimal //= base
    return answer[::-1]

def directionFromDigit(digit: str):
    for key, value in directions.items():
        if digit == value:
            return key

def run(context):
    ui = None
    try:
        app = core.Application.get()
        ui  = app.userInterface

        alert = ui.messageBox
        design: fusion.Design = app.activeProduct
        createPoint = core.Point3D.create
        if not design:
            ui.messageBox('It is not supported in current workspace, please change to MODEL workspace and try again.')
            return

        retVals = ui.inputBox('Please input a blockHash', 'BodyFromHash', '0000000000000000000700ee25d025cf3a2e29706b74b55c0a39d46206c569a2')
        if retVals[0]:
                (hash, isCancelled) = retVals
            
        # Exit the program if the dialog was cancelled.
        if isCancelled:
            return
        base10Hash = int(hash, base=16)
        base6Hash = base(base10Hash, 6)

        root = design.rootComponent
        sketches = root.sketches

        sketch: fusion.Sketch = sketches.add(root.xYConstructionPlane)
        curves = sketch.sketchCurves
        lines = curves.sketchLines
        position = [0,0,0]
        prevPositions = [[0,0,0]]
        # origin = points.add(createPoint(position[0], position[1], 0))
        curvesCollection = core.ObjectCollection.create()

        for item in str(base6Hash):
            direction = directionFromDigit(item)
            
            if direction == 'XPOS': 
                point2 = [position[0] + 1, position[1], position[2]]
            elif direction == 'XNEG':
                point2 = [position[0] - 1, position[1], position[2]]
            elif direction == 'YPOS': 
                point2 = [position[0], position[1] + 1, position[2]]
            elif direction == 'YNEG': 
                point2 = [position[0], position[1] - 1, position[2]]
            elif direction == 'ZPOS': 
                point2 = [position[0], position[1], position[2] + 1]
            elif direction == 'ZNEG': 
                point2 = [position[0], position[1], position[2] - 1]

            if point2 in prevPositions:
                continue
            line = lines.addByTwoPoints(
                createPoint(position[0], position[1], position[2]),
                createPoint(point2[0], point2[1], point2[2])
                )
            if line is None:
                alert('Failed to draw line...')
                return
 
            prevPositions.append(point2)
            position = point2
            curvesCollection.add(line)

        createPipe(root, curvesCollection, 0.2, 0.04)
        app.activeViewport.refresh()

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def createPipe(comp: fusion.Component, curves: fusion.SketchCurves, radius: int, pipeThickness: int):
    # create path
    feats = comp.features
    chainedOption = fusion.ChainedCurveOptions.connectedChainedCurves
    if fusion.BRepEdge.cast(curves):
        chainedOption = fusion.ChainedCurveOptions.tangentChainedCurves
    path = fusion.Path.create(curves, chainedOption)
    path = feats.createPath(curves)
    
    # create profile
    planes = comp.constructionPlanes
    planeInput = planes.createInput()
    planeInput.setByDistanceOnPath(path, core.ValueInput.createByReal(0))
    plane = planes.add(planeInput)
    
    sketches = comp.sketches
    sketch: fusion.Sketch = sketches.add(plane)
    
    center = plane.geometry.origin
    center = sketch.modelToSketchSpace(center)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, radius)
    profile = sketch.profiles[0]
    
    # create sweep
    sweepFeats = feats.sweepFeatures
    sweepInput = sweepFeats.createInput(profile, path, fusion.FeatureOperations.NewBodyFeatureOperation)
    sweepInput.orientation = fusion.SweepOrientationTypes.PerpendicularOrientationType
    sweepFeat = sweepFeats.add(sweepInput)
    
    # create shell
    startFaces = sweepFeat.startFaces
    endFaces = sweepFeat.endFaces
    
    objCol = core.ObjectCollection.create()
    for startFace in startFaces:
        objCol.add(startFace)
    for endFace in endFaces:
        objCol.add(endFace)
    
    if objCol.count == 0:
        bodies = sweepFeat.bodies
        for body in bodies:
            objCol.add(body)
    
    shellFeats = feats.shellFeatures
    shellInput = shellFeats.createInput(objCol, False)
    shellInput.insideThickness = core.ValueInput.createByReal(pipeThickness)
    shellFeats.add(shellInput)
    
