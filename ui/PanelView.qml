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

        RowLayout {
            SpinBox {
                implicitWidth: 48
                from: 0
                to: 1000
                value: root.panel.sensitivity

                onValueModified: {
                    root.panel.sensitivity = value;
                }
            }

            Slider {
                Layout.fillWidth: true
                from: 0
                to: 1000
                value: root.panel.sensitivity

                onMoved: {
                    root.panel.sensitivity = value;
                }
            }
        }

        Item {
            Layout.fillHeight: true
        }
    }
}
