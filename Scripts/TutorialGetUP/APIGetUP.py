#Author-
#Description-

import adsk.core, adsk.fusion, adsk.cam, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        ui.messageBox(ui.activeWorkspace.name)
        design = app.activeProduct
        retParam = design.userParameters.itemByName('length')

        ui.messageBox(retParam.name + ' set to ' + retParam.expression)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
