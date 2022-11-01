#Author-
#Description-

import adsk.core, adsk.fusion, adsk.cam, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        
        pName = 'myParam'
        pUnit = 'mm'
        pExpression = adsk.core.ValueInput.createByReal(5.0)
        design.userParameters.add(pName, pExpression, pUnit, "")

        ui.messageBox('Params updated')
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
