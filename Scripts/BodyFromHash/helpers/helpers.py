import adsk.core as core, adsk.fusion as fusion

directions = {
    'XPOS': '0',
    'XNEG': '1',
    'YPOS': '2',
    'YNEG': '3',
    'ZPOS': '4',
    'ZNEG': '5'
}

# Convert integer to baseX where x <= 36
def base(decimal: int, base: int) :
    if base < 2 or base > 36:
        raise Exception('Supplied base must be between 2 and 36')
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
