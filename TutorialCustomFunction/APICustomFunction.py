#Author-
#Description-

import adsk.core as core, adsk.fusion as fusion, adsk.cam, traceback

app = core.Application.get()
ui  = app.userInterface
alert = ui.messageBox

def customFunc():
    alert('inside customFunc')

def run(context):
    ui = None
    try:
        customFunc()
        alert('run')

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
