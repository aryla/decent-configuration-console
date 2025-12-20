import QtQuick
import QtQuick.Controls

import Model

Page {
    id: root
    property Panel panel
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
    }

    Item {
        id: content
        x: 8
        y: 0
        width: parent.width - 16
        implicitHeight: curve.y + curve.height + sensor0.height + sensor1.height + sensitivity.height + 3 * spacing
        height: implicitHeight

        property int spacing: 8

        CurveView {
            id: curve
            panel: root.panel
            x: 0
            y: 0
            width: parent.width
            height: Math.ceil(parent.width / 2)
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
            y: sensor1.y + sensor1.height + parent.spacing
            width: parent.width
            implicitHeight: sensitivitySpin.implicitHeight
            height: implicitHeight

            Slider {
                id: sensitivitySlider
                x: 0
                y: Math.floor(sensitivitySpin.implicitHeight / 2) - Math.floor(implicitHeight / 2)
                width: parent.width - 48 - 8
                height: implicitHeight
                from: 0
                to: 1000
                value: root.panel.sensitivity

                onMoved: {
                    root.panel.sensitivity = value;
                }
            }

            SpinBox {
                id: sensitivitySpin
                x: parent.width - 48
                y: 0
                width: 48
                height: implicitHeight
                from: 0
                to: 1000
                value: root.panel.sensitivity

                onValueModified: {
                    root.panel.sensitivity = value;
                }
            }
        }
    }
}
