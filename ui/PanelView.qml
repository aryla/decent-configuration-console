import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Model

Page {
    id: root
    property Panel panel
    property bool isMaximized
    property bool isFocused
    property double maximumContentHeight: Layout.maximumHeight - (topPadding + header.implicitHeight + bottomPadding)

    signal focused
    signal maximized
    signal unmaximized

    onActiveFocusChanged: {
        if (activeFocus)
            focused();
    }

    implicitHeight: topPadding + header.height + content.height + bottomPadding
    topPadding: 8
    bottomPadding: 8
    leftPadding: 8
    rightPadding: 8

    background: Rectangle {
        radius: 8
        color: root.panel.pressed ? root.palette.active.light : root.palette.active.window

        Rectangle {
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            height: 1
            width: Math.floor(parent.width / 4)
            color: root.palette.active.highlight
            visible: root.isFocused && !root.isMaximized
        }
    }

    header: Item {
        implicitHeight: 36
        height: implicitHeight
        Label {
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.panel.name
        }

        Button {
            x: parent.x + 8
            y: parent.y + 8
            height: implicitHeight
            width: implicitWidth
            visible: root.isMaximized
            text: "Reset"
            onClicked: root.panel.curve.reset_points()

            hoverEnabled: true
            ToolTip.visible: hovered
            ToolTip.delay: 1000
            ToolTip.text: "Reset curve"
        }

        Button {
            id: maximizeButton
            x: parent.width - 8 - implicitWidth
            y: parent.y + 8
            implicitWidth: 28
            implicitHeight: 28
            height: implicitHeight
            width: implicitWidth
            visible: !root.isMaximized
            text: "Maximize"
            icon.source: "qrc:///icons/maximize.svg"
            display: AbstractButton.IconOnly
            onClicked: root.maximized()

            hoverEnabled: true
            ToolTip.visible: hovered
            ToolTip.delay: 1000
            ToolTip.text: "Maximize\nCtrl+M"
        }

        Button {
            x: parent.width - 8 - implicitWidth
            y: parent.y + 8
            implicitWidth: 28
            implicitHeight: 28
            height: implicitHeight
            width: implicitWidth
            visible: root.isMaximized
            text: "Show all panels"
            icon.source: "qrc:///icons/minimize.svg"
            display: AbstractButton.IconOnly
            onClicked: root.unmaximized()

            hoverEnabled: true
            ToolTip.visible: hovered
            ToolTip.delay: 1000
            ToolTip.text: "Show all panels\nCtrl+M"
        }
    }

    Item {
        id: content
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        implicitHeight: curve.height + controlsColumn.height
        height: implicitHeight

        MouseArea {
            x: -root.leftPadding
            y: -(root.topPadding + root.header.height)
            width: root.width
            height: root.height
            onPressed: root.focused()
        }

        Item {
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            width: curve.width + (root.isMaximized ? band.implicitWidth : 0)
            height: curve.height

            CurveView {
                id: curve
                panel: root.panel
                property int maximumWidth: content.width - (root.isMaximized ? band.implicitWidth : 0)
                property int maximumHeight: root.maximumContentHeight - controlsColumn.height
                x: 0
                y: 0
                height: Math.max(40, Math.min(Math.floor(maximumWidth / 2), maximumHeight))
                width: Math.max(80, Math.min(maximumWidth, 2 * maximumHeight))

                onFocused: root.focused()
            }

            ColumnLayout {
                id: band
                y: 0
                x: curve.x + curve.width
                height: curve.height
                width: 8 + 48 + 8
                spacing: 8
                visible: root.isMaximized

                SpinBox {
                    Layout.alignment: Qt.AlignTop | Qt.AlignLeft
                    Layout.leftMargin: 4
                    implicitWidth: 48
                    from: 0
                    to: 100
                    editable: true
                    value: 100 * root.panel.curve.above / 0.150
                    onValueModified: root.panel.curve.above = value / 100 * 0.150
                }

                Row {
                    Layout.alignment: Qt.AlignVCenter | Qt.AlignLeft
                    Layout.fillHeight: true
                    leftPadding: 8
                    spacing: 8

                    ColumnLayout {
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        spacing: 8

                        Slider {
                            Layout.fillHeight: true
                            orientation: Qt.Vertical
                            from: 0
                            to: 0.150
                            value: root.panel.curve.above
                            onMoved: root.panel.curve.above = value
                        }

                        Slider {
                            id: bandBelow
                            Layout.fillHeight: true
                            orientation: Qt.Vertical
                            transform: Scale {
                                origin.y: bandBelow.height / 2
                                yScale: -1
                            }
                            from: 0
                            to: 0.150
                            value: root.panel.curve.below
                            onMoved: root.panel.curve.below = value
                        }
                    }

                    Item {
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: bandLabel.implicitHeight

                        Label {
                            id: bandLabel
                            anchors.centerIn: parent
                            rotation: 90
                            text: "Hysteresis band"
                        }
                    }
                }

                SpinBox {
                    Layout.alignment: Qt.AlignBottom | Qt.AlignLeft
                    Layout.leftMargin: 4
                    implicitWidth: 48
                    from: -100
                    to: 0
                    editable: true
                    value: -100 * root.panel.curve.below / 0.150
                    onValueModified: root.panel.curve.below = value / -100 * 0.150
                }
            }
        }

        Column {
            id: controlsColumn
            x: 0
            y: curve.height
            width: parent.width
            topPadding: 24

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

            Label {
                anchors.left: parent.left
                anchors.right: parent.right
                leftPadding: 0
                rightPadding: 0
                topPadding: 12
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
                    Layout.preferredHeight: sensitivitySpin.implicitHeight
                    from: 0
                    to: 1
                    value: root.panel.sensitivity
                    onMoved: root.panel.sensitivity = value
                }

                SpinBox {
                    id: sensitivitySpin
                    Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
                    implicitWidth: 48
                    from: 0
                    to: 100
                    editable: true
                    visible: root.isMaximized
                    value: root.panel.sensitivity * 100
                    onValueModified: root.panel.sensitivity = value / 100
                }
            }
        }
    }
}
