import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Model

Page {
    id: root
    property Panel panel

    header: ToolBar {
        Text {
            Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
            text: root.panel.name
        }
    }

    ColumnLayout {
        anchors.fill: parent

        SensorView {
            sensor: root.panel.sensor0
            Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
            Layout.fillWidth: true
        }

        SensorView {
            sensor: root.panel.sensor1
            Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
            Layout.fillWidth: true
        }

        Item {
            Layout.fillHeight: true
        }
    }
}
