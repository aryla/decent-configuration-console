import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Model

Item {
    id: root
    property Sensor sensor
    property bool isMaximized

    implicitHeight: barContainer.implicitHeight

    RowLayout {
        anchors.fill: parent

        SpinBox {
            Layout.alignment: Qt.AlignTop | Qt.AlignLeft
            implicitWidth: 48
            from: 0
            to: root.sensor.range.min_limit * 100
            value: root.sensor.range.min * 100
            editable: true
            visible: root.isMaximized

            onValueModified: {
                root.sensor.range.min = value / 100;
            }
        }

        Item {
            id: barContainer
            Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
            Layout.fillWidth: true
            implicitHeight: bar.implicitHeight + Math.ceil(range.first.implicitHandleHeight / 2) + 3

            ProgressBar {
                id: bar
                x: 0
                y: 1
                width: parent.width
                implicitHeight: 26
                height: implicitHeight
                value: root.sensor.level
            }

            Rectangle {
                y: bar.y
                height: bar.height
                anchors.left: bar.left
                width: root.sensor.range.min * bar.width
                color: "#7f7f7f"
                opacity: 0.8
            }

            Rectangle {
                y: bar.y
                height: bar.height
                anchors.right: bar.right
                width: (1 - root.sensor.range.max) * bar.width
                color: "#7f7f7f"
                opacity: 0.8
            }

            RangeSlider {
                id: range
                x: -Math.floor(first.implicitHandleHeight / 2)
                y: bar.y + bar.height - Math.floor(first.implicitHandleHeight / 2)
                from: 0
                to: 1
                width: parent.width + first.implicitHandleHeight
                first.value: root.sensor.range.min
                second.value: root.sensor.range.max
                background: null

                first.onMoved: {
                    root.sensor.range.min = first.value;
                }

                second.onMoved: {
                    root.sensor.range.max = second.value;
                }
            }

            Label {
                text: root.sensor.name + ":"
                anchors.verticalCenter: bar.verticalCenter
                anchors.right: bar.horizontalCenter
            }

            Label {
                text: (root.sensor.level * 100).toFixed(1)
                anchors.verticalCenter: bar.verticalCenter
                anchors.left: bar.horizontalCenter
                width: 36
                horizontalAlignment: Text.AlignRight
            }
        }

        SpinBox {
            Layout.alignment: Qt.AlignTop | Qt.AlignLeft
            implicitWidth: 48
            from: root.sensor.range.max_limit * 100
            to: 100
            value: root.sensor.range.max * 100
            editable: true
            visible: root.isMaximized

            onValueModified: {
                root.sensor.range.max = value / 100;
            }
        }
    }
}
