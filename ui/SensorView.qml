import QtQuick
import QtQuick.Controls

import Model

Item {
    id: root
    property Sensor sensor
    implicitHeight: spinMin.y + spinMin.height

    ProgressBar {
        id: bar
        x: range.first.implicitHandleWidth / 2
        y: 0
        width: parent.width - range.first.implicitHandleWidth / 2 - range.second.implicitHandleWidth / 2
        height: 24
        implicitHeight: 24
        value: root.sensor.level
    }

    Rectangle {
        y: 0
        height: bar.height
        anchors.left: bar.left
        width: root.sensor.range.min * bar.width
        color: "#777"
        opacity: 0.5
    }

    Rectangle {
        y: 0
        height: bar.height
        anchors.right: bar.right
        width: (1 - root.sensor.range.max) * bar.width
        color: "#777"
        opacity: 0.5
    }

    RangeSlider {
        id: range
        x: 0
        y: bar.height - first.implicitHandleHeight / 2
        from: 0
        to: 1
        width: parent.width
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

    SpinBox {
        id: spinMin
        y: range.y + range.height + 2
        anchors.left: bar.left
        width: 48
        height: implicitHeight
        from: 0
        to: root.sensor.range.min_limit * 100
        value: root.sensor.range.min * 100

        onValueModified: {
            root.sensor.range.min = value / 100;
        }
    }

    SpinBox {
        id: spinMax
        y: range.y + range.height + 2
        anchors.right: bar.right
        width: 48
        height: implicitHeight
        from: root.sensor.range.max_limit * 100
        to: 100
        value: root.sensor.range.max * 100

        onValueModified: {
            root.sensor.range.max = value / 100;
        }
    }

    Label {
        text: root.sensor.name
        anchors.centerIn: bar
    }
}
