#Author-
#Description-

import adsk.core, adsk.fusion, adsk.cam, traceback

def run(context):
    ui = None
    testVal = 3 * 123
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design: adsk.fusion.Design = app.activeProduct
        textPalette = ui.palettes.itemById('TextCommands')
        if not textPalette.isVisible:
            textPalette.isVisible = True
        textPalette.writeText(f'{testVal}')

        rootComp = design.rootComponent

        # Create two new components under root component
        allOccs = rootComp.occurrences
        transform = adsk.core.Matrix3D.create()
        subOcc0 = allOccs.addNewComponent(transform)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
