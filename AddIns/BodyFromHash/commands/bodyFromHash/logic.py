import adsk, adsk.core as core, adsk.fusion as fusion
from .helpers import helpers

app = core.Application.get()
if app:
    ui  = app.userInterface
    createPoint = core.Point3D.create
    alert = ui.messageBox
skipValidate = False

class BodyFromHashLogic():
    def __init__(self) -> None:
        self.hash = '0000000000000000000700ee25d025cf3a2e29706b74b55c0a39d46206c569a2'
        self.base = '16'

    def CreateCommandInputs(self, inputs: core.CommandInputs):
        global skipValidate
        skipValidate = True

        self.hashInput = inputs.addStringValueInput('hash', 'Hash', self.hash)
        self.baseInput = inputs.addStringValueInput('base', 'Base', self.base)
        
        self.errorMessageTextInput = inputs.addTextBoxCommandInput('errMessage', '', '', 2, True)
        self.errorMessageTextInput.isFullWidth = True

        skipValidate = False

    def HandleInputsChanged(self, args: core.InputChangedEventArgs):
        pass

    def HandleValidateInputs(self, args: core.ValidateInputsEventArgs):
        if not skipValidate:
            self.errorMessageTextInput.text = ''

            inputs = args.inputs
            hashInput: core.StringValueCommandInput = inputs.itemById('hash')
            baseInput: core.StringValueCommandInput = inputs.itemById('base')

            # Verify the validity of the input values. This controls if the OK button is enabled or not.
            if len(hashInput.value) == 0:
                args.areInputsValid = False
                self.errorMessageTextInput.text = 'Please provide a hash string'
                return
            if int(baseInput.value) < 2 or int(baseInput.value) > 36:
                args.areInputsValid = False
                self.errorMessageTextInput.text = 'Please provide a base between 2 and 36'
                return

            try:
                int(hashInput.value, int(baseInput.value))
            except Exception as e:
                errMsg: str = e.args[0]
                if errMsg.startswith('invalid literal for int()'):
                    args.areInputsValid = False
                    self.errorMessageTextInput.text = 'Base is not valid for the hash provided'
                    return
                else:
                    raise
            args.areInputsValid = True
            self.hash = hashInput.value
            self.base = baseInput.value

    def HandleExecute(self, args: core.CommandEventArgs):
        # Get a reference to your command's inputs.
        # inputs = args.command.commandInputs

        createBody(self.base, self.hash)


def createBody(base: str, hash: str):
        base10Hash = int(hash, int(base))
        base6Hash = helpers.base(base10Hash, 6)

        design: fusion.Design = app.activeProduct
        root = design.rootComponent

        # Create a new component by creating an occurrence.
        newOcc = root.occurrences.addNewComponent(core.Matrix3D.create())
        newComp = fusion.Component.cast(newOcc.component)
        newComp.name = f'Body from {hash}'

        # Create a new sketch.
        sketches = root.sketches
        xYPlane = root.xYConstructionPlane
        sketch: fusion.Sketch = sketches.add(xYPlane)

        lines = sketch.sketchCurves.sketchLines
        position = [0,0,0]
        prevPositions = [position]

        for char in base6Hash:
            direction = helpers.directionFromDigit(char)
            
            if direction == 'XPOS': 
                nextPoint = [position[0] + 1, position[1], position[2]]
            elif direction == 'XNEG':
                nextPoint = [position[0] - 1, position[1], position[2]]
            elif direction == 'YPOS': 
                nextPoint = [position[0], position[1] + 1, position[2]]
            elif direction == 'YNEG': 
                nextPoint = [position[0], position[1] - 1, position[2]]
            elif direction == 'ZPOS': 
                nextPoint = [position[0], position[1], position[2] + 1]
            elif direction == 'ZNEG': 
                nextPoint = [position[0], position[1], position[2] - 1]

            if nextPoint in prevPositions:
                continue
            line = lines.addByTwoPoints(
                createPoint(position[0], position[1], position[2]),
                createPoint(nextPoint[0], nextPoint[1], nextPoint[2])
                )
            if line is None:
                alert('Failed to draw line...')
                return
 
            prevPositions.append(nextPoint)
            position = nextPoint
            # curvesCollection.add(line)
            # adsk.doEvents()

        curvesCollection = core.ObjectCollection.create()
        for line in lines:
            curvesCollection.add(line)
        helpers.createPipe(newComp, curvesCollection, 0.2, 0.04)
        # app.activeViewport.refresh()