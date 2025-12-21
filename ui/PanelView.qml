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

    implicitHeight: header.height + content.height + 8

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
        implicitHeight: curve.height + spacing + sensor0.height + spacing + sensor1.height + sensitivity.height
        height: implicitHeight

        property int spacing: 8

        CurveView {
            id: curve
            panel: root.panel
            x: 0
            y: 0
            width: parent.width
            height: Math.min(Math.ceil(parent.width / 2), root.maximumHeight - 56 - sensor0.height - sensor1.height - sensitivity.height)
        }

        SensorView {
            id: sensor0
            sensor: root.panel.sensor0
            x: 0
            y: curve.y + curve.height + parent.spacing
            width: parent.width
            height: implicitHeight
        }

        SensorView {
            id: sensor1
            sensor: root.panel.sensor1
            x: 0
            y: sensor0.y + sensor0.height + parent.spacing
            width: parent.width
            height: implicitHeight
        }

        Item {
            id: sensitivity
            x: 0
            y: sensor1.y + sensor1.height
            width: parent.width
            implicitHeight: sensitivityLabel.implicitHeight + sensitivitySpin.implicitHeight
            height: implicitHeight

            Label {
                id: sensitivityLabel
                x: 0
                y: 0
                width: parent.width
                height: implicitHeight
                leftPadding: 0
                rightPadding: 0
                topPadding: 0
                bottomPadding: 0
                horizontalAlignment: Text.AlignHCenter
                text: "Sensitivity"
            }

            Slider {
                id: sensitivitySlider
                x: 0
                y: sensitivitySpin.y + Math.floor(sensitivitySpin.implicitHeight / 2) - Math.floor(implicitHeight / 2)
                width: parent.width - 48 - 8
                height: implicitHeight
                from: 0
                to: 1
                value: root.panel.sensitivity

                onMoved: {
                    root.panel.sensitivity = value;
                }
            }

            SpinBox {
                id: sensitivitySpin
                x: parent.width - 48
                y: sensitivityLabel.height
                width: 48
                height: implicitHeight
                from: 0
                to: 100
                value: root.panel.sensitivity * 100
                editable: true

                onValueModified: {
                    root.panel.sensitivity = value / 100;
                }
            }
        }
    }
}
