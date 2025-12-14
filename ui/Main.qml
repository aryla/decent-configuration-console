import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Model

ApplicationWindow {
    id: root
    width: 800
    height: 400
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
        onTriggered: {
            root.model.profile = 0;
        }
    }

    Action {
        id: selectProfile2
        text: "Profile 2"
        shortcut: "Ctrl+2"
        checkable: true
        checked: root.model.profile == 1
        onTriggered: {
            root.model.profile = 1;
        }
    }

    Action {
        id: selectProfile3
        text: "Profile 3"
        shortcut: "Ctrl+3"
        checkable: true
        checked: root.model.profile == 2
        onTriggered: {
            root.model.profile = 2;
        }
    }

    Action {
        id: selectProfile4
        text: "Profile 4"
        shortcut: "Ctrl+4"
        checkable: true
        checked: root.model.profile == 3
        onTriggered: {
            root.model.profile = 3;
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.topMargin: 8
        spacing: 8

        ButtonGroup {
            buttons: profileButtons.children
            exclusive: true
        }

        RowLayout {
            id: profileButtons
            Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
            spacing: 16

            Button {
                action: selectProfile1
            }
            Button {
                action: selectProfile2
            }
            Button {
                action: selectProfile3
            }
            Button {
                action: selectProfile4
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
