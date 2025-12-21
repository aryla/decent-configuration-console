import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Model

Page {
    id: root
    property Panel panel
    property bool isMaximized
    property double maximumHeight: Layout.maximumHeight

    signal focused
    signal maximized
    signal unmaximized

    onActiveFocusChanged: {
        if (activeFocus)
            focused();
    }

    implicitHeight: header.height + content.height

    background: Rectangle {
        radius: 8
        color: root.panel.pressed ? root.palette.active.light : root.palette.active.window
    }

    header: Item {
        height: 32
        Label {
            anchors.centerIn: parent
            text: root.panel.name
        }

        Button {
            x: parent.width - 8 - implicitWidth
            y: Math.floor(parent.height / 2) - Math.floor(implicitHeight / 2)
            implicitWidth: implicitHeight
            height: implicitHeight
            width: implicitWidth
            visible: !root.isMaximized
            text: "M"
            onClicked: root.maximized()
        }

        Button {
            x: parent.width - 8 - implicitWidth
            y: Math.floor(parent.height / 2) - Math.floor(implicitHeight / 2)
            height: implicitHeight
            width: implicitWidth
            visible: root.isMaximized
            text: "Back"
            onClicked: root.unmaximized()
        }
    }

    Item {
        id: content
        x: 8
        y: 0
        width: parent.width - 16
        implicitHeight: curve.height + controlsColumn.height + 16
        height: implicitHeight

        CurveView {
            id: curve
            panel: root.panel
            x: 0
            y: 0
            width: parent.width
            height: Math.min(Math.ceil(parent.width / 2), root.maximumHeight - 56 - controlsColumn.height)
        }

        Column {
            id: controlsColumn
            x: 0
            y: curve.height + 8
            width: parent.width
            spacing: 8

            ColumnLayout {
                anchors.left: parent.left
                anchors.right: parent.right
                spacing: 16
                Repeater {
                    model: 2
                    SensorView {
                        Layout.fillWidth: true
                        required property int index
                        sensor: root.panel.sensors[index]
                        isMaximized: root.isMaximized
                    }
                }
            }

            Item {
                implicitHeight: 8
            }

            Label {
                anchors.left: parent.left
                anchors.right: parent.right
                leftPadding: 0
                rightPadding: 0
                topPadding: 0
                bottomPadding: 0
                horizontalAlignment: Text.AlignHCenter
                text: "Sensitivity"
            }

            RowLayout {
                anchors.left: parent.left
                anchors.right: parent.right
                spacing: 8

                Item {
                    implicitWidth: 48
                    visible: root.isMaximized
                }

                Slider {
                    Layout.alignment: Qt.AlignVCenter | Qt.AlignLeft
                    Layout.fillWidth: true
                    from: 0
                    to: 1
                    value: root.panel.sensitivity

                    onMoved: {
                        root.panel.sensitivity = value;
                    }
                }

                SpinBox {
                    Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
                    implicitWidth: 48
                    from: 0
                    to: 100
                    value: root.panel.sensitivity * 100
                    editable: true
                    visible: root.isMaximized

                    onValueModified: {
                        root.panel.sensitivity = value / 100;
                    }
                }
            }
        }
    }
}
