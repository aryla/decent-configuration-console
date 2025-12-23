import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Model

Button {
    id: root
    property int profileId
    property Model model
    checked: root.model.profile == root.profileId

    hoverEnabled: true
    ToolTip.visible: hovered
    ToolTip.delay: 1000
    ToolTip.text: `Switch to profile ${profileId + 1}\n${action.shortcut}`

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

    Popup {
        id: confirmationDialog
        parent: Overlay.overlay
        anchors.centerIn: parent
        modal: true
        focus: true
        topPadding: 16
        bottomPadding: 16
        leftPadding: 16
        rightPadding: 16
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

        Overlay.modal: Rectangle {
            color: "#7f000000"
        }

        Component.onCompleted: {
            root.model.connected_changed.connect(function () {
                if (!root.model.connected) {
                    confirmationDialog.close();
                }
            });
        }

        ColumnLayout {
            spacing: 8

            Label {
                text: "Save changes?"
            }

            Row {
                spacing: 8

                Button {
                    text: "Save"
                    onClicked: {
                        confirmationDialog.close();
                        root.model.save_changes();
                        root.model.profile = root.profileId;
                    }
                }

                Button {
                    text: "Discard"
                    onClicked: {
                        confirmationDialog.close();
                        root.model.revert_changes();
                        root.model.profile = root.profileId;
                    }
                }

                Button {
                    text: "Cancel"
                    onClicked: {
                        confirmationDialog.close();
                    }
                }
            }
        }
    }
}
