import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

import Model

Button {
    id: root
    property int profileId
    property Model model
    checked: root.model.profile == root.profileId

    action: Action {
        text: `Profile ${root.profileId + 1}`
        shortcut: `Ctrl+${root.profileId + 1}`
        onTriggered: {
            if (root.model.has_changes) {
                confirmationDialog.open();
            } else {
                root.model.profile = root.profileId;
            }
        }
    }

    MessageDialog {
        id: confirmationDialog
        text: "You have unsaved changes."
        informativeText: "Do you want to save your changes?"
        buttons: MessageDialog.Save | MessageDialog.Discard | MessageDialog.Cancel
        onButtonClicked: function (button, role) {
            switch (button) {
            case MessageDialog.Save:
                root.model.save_changes();
                root.model.profile = root.profileId;
                break;
            case MessageDialog.Discard:
                root.model.revert_changes();
                root.model.profile = root.profileId;
                break;
            case MessageDialog.Cancel:
                break;
            }
        }
    }
}
