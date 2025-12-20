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

        Item {
            Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
            Layout.fillWidth: true
            implicitHeight: 0.5 * width

            GraphsView {
                id: graph
                anchors.fill: parent
                marginBottom: 4
                marginLeft: 8
                marginRight: 8
                marginTop: 4

                theme: GraphsTheme {
                    colorScheme: GraphsTheme.ColorScheme.Dark
                    backgroundVisible: false
                    // plotAreaBackgroundColor: '#333'
                    grid.mainWidth: 1
                    // grid.mainColor: '#777'
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
                    color: '#bb88aa99'
                    borderWidth: 0

                    lowerSeries: LineSeries {
                        function updatePoints() {
                            const below = root.panel.curve.below;
                            const points = [];
                            for (let i = 0; i < curve.count; i++) {
                                const p = curve.at(i);
                                points.push(Qt.point(p.x, p.y - below));
                            }
                            replace(points);
                        }

                        Component.onCompleted: {
                            root.panel.curve.below_changed.connect(updatePoints);
                            curve.pointReplaced.connect(updatePoints);
                            curve.pointsAdded.connect(updatePoints);
                            curve.pointsReplaced.connect(updatePoints);
                        }
                    }

                    upperSeries: LineSeries {
                        function updatePoints() {
                            const above = root.panel.curve.above;
                            const points = [];
                            for (let i = 0; i < curve.count; i++) {
                                const p = curve.at(i);
                                points.push(Qt.point(p.x, p.y + above));
                            }
                            replace(points);
                        }

                        Component.onCompleted: {
                            root.panel.curve.above_changed.connect(updatePoints);
                            curve.pointReplaced.connect(updatePoints);
                            curve.pointsAdded.connect(updatePoints);
                            curve.pointsReplaced.connect(updatePoints);
                        }
                    }
                }

                LineSeries {
                    id: curve
                    color: '#eee'

                    pointDelegate: Rectangle {
                        property bool pointSelected
                        property int size: pointSelected ? 16 : 8
                        width: size
                        height: size
                        radius: size / 2
                        color: pointSelected ? '#fff' : '#eee'
                    }

                    function updatePoints() {
                        replace(root.panel.curve.points);
                    }

                    Component.onCompleted: {
                        root.panel.curve.points_changed.connect(function () {
                            graphMouseArea.cancelDrag();
                            updatePoints();
                        });
                    }
                }

                ScatterSeries {
                    pointDelegate: Rectangle {
                        width: 8
                        height: 8
                        color: '#f00'
                        radius: 4
                    }

                    Component.onCompleted: {
                        root.panel.dot_changed.connect(function () {
                            replace([root.panel.dot]);
                        });
                    }
                }

                ScatterSeries {
                    id: newPointIndicator
                    visible: false

                    pointDelegate: Rectangle {
                        property int size: 16
                        width: size
                        height: size
                        radius: size / 2
                        color: '#fff'

                        Text {
                            anchors.centerIn: parent
                            text: "+"
                            color: '#000'
                        }
                    }

                    function show(point) {
                        replace([point]);
                        visible = true;
                    }

                    function hide() {
                        visible = false;
                    }
                }
            }

            MouseArea {
                id: graphMouseArea
                anchors.fill: graph
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
                property int pointMinCount: 2
                property int pointMaxCount: 10
                property double pointMinDeltaX: 0.011
                property double dragMaxDistance: 0.05

                property int dragPointIndex: -1
                property bool dragIsNewPoint: false

                function dragActive() {
                    return dragPointIndex >= 0;
                }

                function cancelDrag() {
                    if (!dragActive())
                        return;
                    dragPointIndex = -1;
                    curve.updatePoints();
                }

                function dataCoords(mouse) {
                    const coords = curve.dataPointCoordinatesAt(
                        mouse.x - graph.plotArea.x,
                        mouse.y - graph.plotArea.y);
                    let x = Math.max(-1.0, Math.min(1.0, coords.x));
                    let y = Math.max(0.0, Math.min(1.0, coords.y));
                    if (dragActive() && dragPointIndex - 1 >= 0) {
                        x = Math.max(x, curve.at(dragPointIndex - 1).x + pointMinDeltaX);
                    }
                    if (dragActive() && dragPointIndex + 1 < curve.count) {
                        x = Math.min(x, curve.at(dragPointIndex + 1).x - pointMinDeltaX);
                    }

                    return Qt.point(x, y);
                }

                function nearestPoint(mouse) {
                    const coords = dataCoords(mouse);
                    let nearest = null;
                    for (let index = 0; index < curve.count; index++) {
                        const point = curve.at(index);
                        const dx = coords.x - point.x;
                        const dy = coords.y - point.y;
                        const distance = dx * dx + dy * dy;
                        if (!nearest || distance < nearest.distance) {
                            nearest = {
                                distance,
                                point,
                                index
                            };
                        }
                    }
                    if (nearest.distance > dragMaxDistance)
                        return null;
                    return nearest;
                }

                function newPoint(mouse) {
                    if (curve.count >= pointMaxCount)
                        return null;

                    const coords = dataCoords(mouse);
                    coords.x = Math.max(-1.0, Math.min(1.0, coords.x));
                    coords.y = Math.max(0.0, Math.min(1.0, coords.y));

                    if (curve.count === 0 || coords.x <= curve.at(0).x - pointMinDeltaX) {
                        return {
                            index: 0,
                            point: coords
                        };
                    }

                    if (coords.x >= curve.at(curve.count - 1).x + pointMinDeltaX) {
                        return {
                            index: curve.count,
                            point: coords
                        };
                    }

                    for (let i = 1; i < curve.count; i++) {
                        const left = curve.at(i - 1).x + pointMinDeltaX;
                        const right = curve.at(i).x - pointMinDeltaX;
                        if (coords.x >= left && coords.x <= right) {
                            return {
                                index: i,
                                point: coords
                            };
                        }
                    }

                    return null;
                }

                function highlightPoint(index) {
                    highlightClear();
                    curve.selectPoint(index);
                }

                function highlightNewPoint(coords) {
                    highlightClear();
                    newPointIndicator.show(coords);
                }

                function highlightClear() {
                    newPointIndicator.hide();
                    curve.deselectAllPoints();
                }

                onPressed: mouse => {
                    if (dragActive() && mouse.button !== Qt.LeftButton) {
                        cancelDrag();
                        return;
                    }
                    if (dragActive())
                        return;

                    if (mouse.button === Qt.LeftButton) {
                        let point = null;
                        if ((point = nearestPoint(mouse))) {
                            dragIsNewPoint = false;
                        } else if ((point = newPoint(mouse))) {
                            dragIsNewPoint = true;
                            curve.insert(point.index, dataCoords(mouse));
                        }

                        if (point) {
                            dragPointIndex = point.index;
                            curve.replace(dragPointIndex, dataCoords(mouse));
                            highlightPoint(dragPointIndex);
                            mouse.accepted = true;
                        }
                    } else if (mouse.button === Qt.MiddleButton) {
                        let point = null;
                        if (curve.count > pointMinCount && (point = nearestPoint(mouse))) {
                            highlightClear();
                            root.panel.curve.remove_point(point.index);
                        }
                    }
                }

                onPositionChanged: mouse => {
                    let point = null;
                    if (dragActive()) {
                        curve.replace(dragPointIndex, dataCoords(mouse));
                    } else if ((point = nearestPoint(mouse))) {
                        highlightPoint(point.index);
                    } else if ((point = newPoint(mouse))) {
                        highlightNewPoint(point.point);
                    } else {
                        highlightClear();
                    }
                }

                onReleased: mouse => {
                    if (!dragActive())
                        return;
                    const coords = dataCoords(mouse);
                    curve.replace(dragPointIndex, coords);

                    if (dragIsNewPoint) {
                        root.panel.curve.add_point(dragPointIndex, coords.x, coords.y);
                    } else {
                        root.panel.curve.move_point(dragPointIndex, coords.x, coords.y);
                    }
                    dragPointIndex = -1;
                }

                onExited: {
                    if (!dragActive()) highlightClear();
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
