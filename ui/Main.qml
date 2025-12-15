import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Model

ApplicationWindow {
    id: root
    width: 960
    height: 540
    visible: true
    title: "Decent Configuration Console"

    property Model model

    header: ToolBar {}

    footer: ToolBar {
        Text {
            Layout.alignment: Qt.AlignVCenter | Qt.AlignLeft
            text: root.model.message
        }
    }

    Action {
        id: selectProfile1
        text: "Profile 1"
        shortcut: "Ctrl+1"
        checkable: true
        checked: root.model.profile == 0
        onTriggered: root.model.profile = 0
    }

    Action {
        id: selectProfile2
        text: "Profile 2"
        shortcut: "Ctrl+2"
        checkable: true
        checked: root.model.profile == 1
        onTriggered: root.model.profile = 1
    }

    Action {
        id: selectProfile3
        text: "Profile 3"
        shortcut: "Ctrl+3"
        checkable: true
        checked: root.model.profile == 2
        onTriggered: root.model.profile = 2
    }

    Action {
        id: selectProfile4
        text: "Profile 4"
        shortcut: "Ctrl+4"
        checkable: true
        checked: root.model.profile == 3
        onTriggered: root.model.profile = 3
    }

    Action {
        id: saveChanges
        text: "Save changes"
        shortcut: "Ctrl+S"
        enabled: root.model.has_changes
        onTriggered: root.model.save_changes()
    }

    Action {
        id: revertChanges
        text: "Revert changes"
        shortcut: "Ctrl+Z"
        enabled: root.model.has_changes
        onTriggered: root.model.revert_changes()
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.topMargin: 8
        spacing: 8

        RowLayout {
            Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
            Layout.fillWidth: true
            Layout.leftMargin: 16
            Layout.rightMargin: 16

            spacing: 16

            Item {
                Layout.fillWidth: true
                Layout.horizontalStretchFactor: 1089
            }

            ButtonGroup {
                exclusive: true
                buttons: [buttonProfile1, buttonProfile2, buttonProfile3, buttonProfile4]
            }

            Button {
                id: buttonProfile1
                action: selectProfile1
            }

            Button {
                id: buttonProfile2
                action: selectProfile2
            }

            Button {
                id: buttonProfile3
                action: selectProfile3
            }

            Button {
                id: buttonProfile4
                action: selectProfile4
            }

            Item {
                Layout.fillWidth: true
                Layout.horizontalStretchFactor: 868
            }

            Button {
                action: saveChanges
            }
            Button {
                action: revertChanges
            }
        }

        RowLayout {
            Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
            uniformCellSizes: true
            spacing: 8

            PanelView {
                Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
                Layout.fillWidth: true
                Layout.fillHeight: true
                panel: root.model.panel0
            }

            PanelView {
                Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
                Layout.fillWidth: true
                Layout.fillHeight: true
                panel: root.model.panel1
            }

            PanelView {
                Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
                Layout.fillWidth: true
                Layout.fillHeight: true
                panel: root.model.panel2
            }

            PanelView {
                Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
                Layout.fillWidth: true
                Layout.fillHeight: true
                panel: root.model.panel3
            }
        }
    }
}
