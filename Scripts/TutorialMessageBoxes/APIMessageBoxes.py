# Author-
# Description-

import adsk.core as core
import adsk.fusion as fusion
import adsk.cam
import traceback


def run(context):
    ui = None
    try:
        app = core.Application.get()
        ui = app.userInterface
        alert = ui.messageBox

        buttons = core.MessageBoxButtonTypes
        icons = core.MessageBoxIconTypes
        dialogResults = core.DialogResults

        # userResponse = alert('OK', 'Title', buttons.YesNoCancelButtonType,
        #               icons.WarningIconType)
        # if userResponse == dialogResults.DialogCancel:
        #     alert('You cancelled!')
        # elif userResponse == dialogResults.DialogError:
        #     alert('ERROR!')
        # elif userResponse == dialogResults.DialogNo:
        #     alert('You said no!')
        # elif userResponse == dialogResults.DialogOK:
        #     alert('Everything is peachy!')
        # elif userResponse == dialogResults.DialogYes:
        #     alert('Sounds good!')

        defaultInput = 'No Name'
        userInput = ui.inputBox('Enter a name', 'Name input', defaultInput)
        if userInput[1]: 
            return   
        if userInput[0] == defaultInput:
            alert('Too lazy?')
            userInput = alert('Want to try again?', 'Try again', buttons.YesNoButtonType)
            if userInput == dialogResults.DialogYes:
                userInput = ui.inputBox('Enter a name', 'Name input', defaultInput)
            else:
                userInput = [defaultInput, True]
        alert(userInput[0])

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
