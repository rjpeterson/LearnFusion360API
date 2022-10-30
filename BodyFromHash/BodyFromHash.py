#Author-
#Description-

import adsk.core as core, adsk.fusion as fusion, adsk.cam, traceback

defaultHash = '0000000000000000000700ee25d025cf3a2e29706b74b55c0a39d46206c569a2'
defaultBase = '16'


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

handlers = []
createPoint = core.Point3D.create
app = core.Application.get()
if app:
    ui  = app.userInterface
    alert = ui.messageBox

class BodyFromHashExecuteHandler(core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args: core.CommandEventArgs):
        try:
            unitsMgr = app.activeProduct.unitsManager
            command: core.Command = args.firingEvent.sender
            inputs = command.commandInputs

            bodyFromHash = BodyFromHash()
            for input in inputs:
                if input.id == 'hash':
                    bodyFromHash.hash = input.value
                elif input.id == 'base':
                    bodyFromHash.base = input.value

            bodyFromHash.createBody()
            args.isValidResult = True
        except:
            if ui:
                alert('Failed:\n{}'.format(traceback.format_exc()))

class BodyFromHashDestroyHandler(core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # when the command is done, terminate the script
            # this will release all globals which will remove all event handlers
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class BodyFromHashCommandCreatedHandler(core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args: core.CommandCreatedEventArgs):
        try:
            cmd = args.command
            cmd.isRepeatable = False
            onExecute = BodyFromHashExecuteHandler()
            cmd.execute.add(onExecute)
            onExecutePreview = BodyFromHashExecuteHandler()
            cmd.executePreview.add(onExecutePreview)
            onDestroy = BodyFromHashDestroyHandler()
            cmd.destroy.add(onDestroy)
            # keep the handlers referenced beyond this function
            handlers.append(onExecute)
            handlers.append(onExecutePreview)
            handlers.append(onDestroy)

            inputs = cmd.commandInputs
            inputs.addStringValueInput('hash', 'Hash', defaultHash)
            inputs.addStringValueInput('base', 'Base', defaultBase)

        except:
            if ui:
                alert('Failed:\n{}'.format(traceback.format_exc()))

class BodyFromHash:
    def __init__(self):
        self._hash = defaultHash
        self._base = defaultBase

    #properties
    @property
    def hash(self):
        return self._hash
    @hash.setter
    def hash(self, value):
        self._hash = value
    
    @property
    def base(self):
        return self._base
    @base.setter
    def base(self, value):
        self._base = value

    def createBody(self):
        base10Hash = int(self._hash, int(self._base))
        base6Hash = base(base10Hash, 6)

        design: fusion.Design = app.activeProduct
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

    

def run(context):
    try:
        design: fusion.Design = app.activeProduct
        if not design:
            ui.messageBox('It is not supported in current workspace, please change to MODEL workspace and try again.')
            return
        commandDefinitions = ui.commandDefinitions
        #check the command exists or not
        cmdDef = commandDefinitions.itemById('BodyFromHash')
        if not cmdDef:
            cmdDef = commandDefinitions.addButtonDefinition('BodyFromHash',
                    'Create Body from a Hash',
                    'Create a body from a hash.',
                    './resources') # relative resource file path is specified

        onCommandCreated = BodyFromHashCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        # keep the handler referenced beyond this function
        handlers.append(onCommandCreated)
        inputs = adsk.core.NamedValues.create()
        cmdDef.execute(inputs)

        # prevent this module from being terminate when the script returns, because we are waiting for event handlers to fire
        adsk.autoTerminate(False)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

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
