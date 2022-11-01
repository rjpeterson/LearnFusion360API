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
    inputParam = "Length"
    inputVal = "5 mm"
    isValid = False
    while not isValid:
        param = ui.inputBox('Enter an param Name', 'New Param', inputParam)
        val = ui.inputBox('Enter an input value', 'New Param', inputVal)
        if param[0] and val[0]:
            (inputParam, isCanceled1) = param
            (inputVal, isCanceled2) = val
        if isCanceled1 or isCanceled2:
            return
        unitsMgr = design.unitsManager
        try:
            # validatedInput = unitsMgr.evaluateExpression(inputVal, unitsMgr.defaultLengthUnits)
            validatedInput = unitsMgr.evaluateExpression(inputVal, unitsMgr.defaultLengthUnits)
            isValid = True
            # ui.messageBox(f'User Param: {validatedInput}')
        except:
            ui.messageBox('"' + inputVal + '" is not a valid input', 'Invalid Input', adsk.core.MessageBoxButtonTypes.OKButtonType, adsk.core.MessageBoxIconTypes.CriticalIconType)
            isValid = False
    
    realInput = adsk.core.ValueInput.createByReal(validatedInput)
    # design.userParameters.add(param[0], realInput, unitsMgr.defaultLengthUnits, '')
    design.userParameters.add(param[0], realInput, unitsMgr.defaultLengthUnits, '')
            

    
    
    # ui.messageBox(newInput[0])