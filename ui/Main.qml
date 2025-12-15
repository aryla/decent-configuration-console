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

            ProfileView {
                profileId: 0
                model: root.model
            }

            ProfileView {
                profileId: 1
                model: root.model
            }

            ProfileView {
                profileId: 2
                model: root.model
            }

            ProfileView {
                profileId: 3
                model: root.model
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
