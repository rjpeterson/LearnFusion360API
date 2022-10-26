#Author-
#Description-

import adsk.core, adsk.fusion, adsk.cam, traceback

def run(context):
    ui = None

    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)

        getUserInput(ui, design)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def getUserInput(ui: adsk.core.UserInterface, design: adsk.fusion.Design):
    inputAngle = 2
    inputName = 'Draft'
    inputThickness = 2
    inputThicknessName = 'WallThickness'
    inputWallThickness = 'WallThickness * 0.6'
    inputWallThicknessName = 'InternalWallThickness'
    unitsMgr = design.unitsManager

    inputAngle = unitsMgr.evaluateExpression(str(inputAngle), 'deg')
    inputThickness = unitsMgr.evaluateExpression(str(inputThickness), 'mm')
    # inputWallThickness = unitsMgr.evaluateExpression(str(inputWallThickness), 'mm')

    inputAngle = adsk.core.ValueInput.createByReal(inputAngle)
    inputThickness = adsk.core.ValueInput.createByReal(inputThickness)
    inputWallThickness = adsk.core.ValueInput.createByString(inputWallThickness)

    design.userParameters.add(inputName, inputAngle, 'deg', '')
    design.userParameters.add(inputThicknessName, inputThickness, 'mm', '')
    design.userParameters.add(inputWallThicknessName, inputWallThickness, 'mm', '')
    # inputParam = 'Length'
    # inputVal = '5 mm'
    # isValid = False

    # while not isValid:
    #     param = ui.inputBox('Enter an p'New Param', inputParam)
    #     val = ui.inputBox('Enter an input value', 'New Paaram Name', ram', inputVal)
    #     if param[0] and val[0]:
    #         (inputParam, isCanceled1) = param
    #         (inputVal, isCanceled2) = val
    #     if isCanceled1 or isCanceled2:
    #         return
    #     unitsMgr = design.unitsManager
    #     try:
    #         # validatedInput = unitsMgr.evaluateExpression(inputVal, unitsMgr.defaultLengthUnits)
    #         validatedInput = unitsMgr.evaluateExpression(inputVal, unitsMgr.defaultLengthUnits)
    #         isValid = True
    #         # ui.messageBox(f'User Param: {validatedInput}')
    #     except:
    #         ui.messageBox('"' + inputVal + '" is not a valid input', 'Invalid Input', adsk.core.MessageBoxButtonTypes.OKButtonType, adsk.core.MessageBoxIconTypes.CriticalIconType)
    #         isValid = False
    
    # realInput = adsk.core.ValueInput.createByReal(validatedInput)
    # # design.userParameters.add(param[0], realInput, unitsMgr.defaultLengthUnits, '')
    # design.userParameters.add(param[0], realInput, unitsMgr.defaultLengthUnits, '')
            