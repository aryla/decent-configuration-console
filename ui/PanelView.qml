import QtGraphs
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

        GraphsView {
            Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
            Layout.fillWidth: true
            implicitHeight: 0.5 * width
            marginBottom: 4
            marginLeft: 8
            marginRight: 8
            marginTop: 4

            theme: GraphsTheme {
                theme: GraphsTheme.Theme.UserDefined
                backgroundVisible: false
                plotAreaBackgroundColor: '#333'
                grid.mainWidth: 1
                grid.mainColor: '#777'
            }

            axisX: ValueAxis {
                id: xAxis
                min: -1
                max: 1
                tickInterval: 0.2
                labelsVisible: false
                titleVisible: false
                visible: false
            }

            axisY: ValueAxis {
                id: yAxis
                min: 0
                max: 1
                tickInterval: 0.2
                labelsVisible: false
                titleVisible: false
                visible: false
            }

            AreaSeries {
                color: '#8a9'
                opacity: 0.8
                borderWidth: 0

                lowerSeries: LineSeries {
                    function updatePoints() {
                        const below = root.panel.curve.below;
                        replace(root.panel.curve.points.map(p => Qt.point(p.x, p.y - below)));
                    }

                    Component.onCompleted: {
                        root.panel.curve.below_changed.connect(updatePoints);
                        root.panel.curve.points_changed.connect(updatePoints);
                    }
                }

                upperSeries: LineSeries {
                    function updatePoints() {
                        const above = root.panel.curve.above;
                        replace(root.panel.curve.points.map(p => Qt.point(p.x, p.y + above)));
                    }

                    Component.onCompleted: {
                        root.panel.curve.above_changed.connect(updatePoints);
                        root.panel.curve.points_changed.connect(updatePoints);
                    }
                }
            }

            LineSeries {
                color: '#eee'

                pointDelegate: Rectangle {
                    width: 8
                    height: 8
                    color: '#eee'
                    radius: 4
                }

                Component.onCompleted: {
                    root.panel.curve.points_changed.connect(function () {
                        replace(root.panel.curve.points);
                    });
                }
            }

            ScatterSeries {
                pointDelegate: Rectangle {
                    width: 8
                    height: 8
                    color: '#48f'
                    radius: 4
                }

                Component.onCompleted: {
                    root.panel.dot_changed.connect(function () {
                        replace([root.panel.dot]);
                    });
                }
            }
        }

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
