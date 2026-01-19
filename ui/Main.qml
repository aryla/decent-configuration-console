import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Model

ApplicationWindow {
    id: root
    width: 960
    height: 540
    minimumWidth: 720
    minimumHeight: 520
    visible: true

    property Model model
    property int focusedPanel: 0
    property bool maximized: false

    Shortcut {
        sequences: ["Ctrl+Left"]
        onActivated: root.focusedPanel = 0
    }

    Shortcut {
        sequences: ["Ctrl+Down"]
        onActivated: root.focusedPanel = 1
    }

    Shortcut {
        sequences: ["Ctrl+Up"]
        onActivated: root.focusedPanel = 2
    }

    Shortcut {
        sequences: ["Ctrl+Right"]
        onActivated: root.focusedPanel = 3
    }

    Shortcut {
        sequences: ["Ctrl+M"]
        onActivated: root.maximized = !root.maximized
    }

    Shortcut {
        sequences: ["Ctrl++", "Ctrl+="]
        onActivated: root.model.panels[root.focusedPanel].sensitivity += 0.02
    }

    Shortcut {
        sequences: ["Ctrl+-"]
        onActivated: root.model.panels[root.focusedPanel].sensitivity -= 0.02
    }

    header: ToolBar {
        topPadding: 8
        bottomPadding: 8
        leftPadding: 8
        rightPadding: 8

        RowLayout {
            anchors.fill: parent

            Label {
                visible: root.model.connected
                text: "Pad: "
            }
            Button {
                visible: root.model.connected
                text: root.model.alias
                font.family: "monospace"
                onClicked: padInfo.open()

                hoverEnabled: true
                ToolTip.visible: hovered
                ToolTip.delay: 1000
                ToolTip.text: "View pad info"

                Popup {
                    id: padInfo
                    modal: true
                    focus: true
                    topPadding: 16
                    bottomPadding: 16
                    leftPadding: 16
                    rightPadding: 16
                    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

                    Overlay.modal: Rectangle {
                        color: "#7f000000"
                    }

                    Component.onCompleted: {
                        root.model.connected_changed.connect(function () {
                            if (!root.model.connected) {
                                padInfo.close();
                            }
                        });
                    }

                    ColumnLayout {
                        spacing: 8
                        GridLayout {
                            columns: 2
                            uniformCellHeights: true

                            Label {
                                text: "Alias:"
                            }

                            TextField {
                                Layout.fillWidth: true
                                text: root.model.alias
                                maximumLength: 30
                                font.family: "monospace"
                                onEditingFinished: root.model.alias = text
                                placeholderText: "Unnamed"
                            }

                            Label {
                                text: "Mode:"
                            }

                            Row {
                                spacing: 8
                                Button {
                                    checked: root.model.hidmode == 2
                                    text: "Joystick"
                                    onClicked: root.model.hidmode = 2
                                }

                                Button {
                                    checked: root.model.hidmode == 1
                                    text: "Keyboard"
                                    onClicked: root.model.hidmode = 1
                                }

                                Button {
                                    checked: root.model.hidmode == 0
                                    text: "Hidden"
                                    onClicked: root.model.hidmode = 0
                                }
                            }

                            Label {
                                text: "Serial:"
                            }

                            Label {
                                text: root.model.serial
                                font.family: "monospace"
                            }
                        }

                        Button {
                            Layout.alignment: Qt.AlignTop | Qt.AlignRight
                            text: "OK"
                            onClicked: {
                                padInfo.close();
                            }
                        }
                    }
                }
            }

            Button {
                visible: root.model.connected
                text: "Disconnect"
                onClicked: root.model.do_disconnect()
            }

            Button {
                visible: !root.model.connected
                text: "Connect"
                onClicked: root.model.do_connect()
            }

            Item {
                Layout.fillWidth: true
            }

            Button {
                text: "About"
                onClicked: aboutDialog.open()

                Popup {
                    id: aboutDialog
                    parent: Overlay.overlay
                    anchors.centerIn: parent
                    modal: true
                    focus: true
                    topPadding: 16
                    bottomPadding: 16
                    leftPadding: 16
                    rightPadding: 16
                    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

                    Overlay.modal: Rectangle {
                        color: "#7f000000"
                    }

                    ColumnLayout {
                        spacing: 8

                        RowLayout {
                            spacing: 16

                            Image {
                                Layout.preferredHeight: 128
                                Layout.preferredWidth: 128
                                source: "qrc:///decent.svg"
                                smooth: false
                            }

                            ColumnLayout {
                                Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
                                Layout.rightMargin: 16
                                spacing: 2

                                Label {
                                    text: root.model.app.title
                                    font.pixelSize: 24
                                    font.bold: true
                                    bottomPadding: 8
                                }

                                Label {
                                    Layout.alignment: Qt.AlignTop | Qt.AlignLeft
                                    text: "<a href=\"https://github.com/aryla/decent-configuration-console\">github.com/aryla/decent-configuration-console</a>"
                                    onLinkActivated: link => Qt.openUrlExternally(link)

                                    MouseArea {
                                        anchors.fill: parent
                                        cursorShape: Qt.PointingHandCursor
                                        acceptedButtons: Qt.NoButton
                                    }
                                }

                                Row {
                                    Layout.alignment: Qt.AlignTop | Qt.AlignLeft


                                    Label {
                                        text: "Version " + root.model.app.version
                                    }

                                    Label {
                                        text: " (" + root.model.app.detailed_version + ")"
                                        visible: root.model.app.detailed_version != '' && root.model.app.detailed_version != 'v' + root.model.app.version
                                    }

                                }

                                Label {
                                    Layout.alignment: Qt.AlignTop | Qt.AlignLeft
                                    text: "Built on " + root.model.app.build_date
                                }
                            }
                        }

                        Button {
                            Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
                            text: "Close"
                            onClicked: aboutDialog.close()
                        }
                    }
                }
            }

            Button {
                text: "Quit"
                onClicked: root.close()
            }
        }
    }

    footer: ToolBar {
        Label {
            Layout.alignment: Qt.AlignVCenter | Qt.AlignLeft
            text: root.model.message
        }
    }

    Rectangle {
        anchors.fill: parent
        color: root.palette.active.base

        StackLayout {
            id: mainStack
            anchors.fill: parent
            currentIndex: root.model.connected ? 1 : 0

            Item {
                Page {
                    anchors.centerIn: parent
                    topPadding: 16
                    bottomPadding: 16
                    leftPadding: 16
                    rightPadding: 16

                    background: Rectangle {
                        radius: 8
                        color: root.palette.active.window
                    }

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 8

                        Label {
                            Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
                            text: "No pad connected."
                        }

                        Button {
                            Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
                            text: "Connect"
                            onClicked: root.model.do_connect()
                        }
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 8

                RowLayout {
                    id: profileRow
                    Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
                    Layout.fillWidth: true
                    Layout.topMargin: 8
                    Layout.leftMargin: 8
                    Layout.rightMargin: 8
                    spacing: 0

                    Item {
                        implicitWidth: buttonsRow.implicitWidth
                    }

                    Item {
                        Layout.minimumWidth: 8
                        Layout.fillWidth: true
                    }

                    Row {
                        Layout.alignment: Qt.AlignTop | Qt.AlignRight
                        spacing: 8

                        Repeater {
                            model: 4
                            ProfileView {
                                required property int index
                                profileId: index
                                model: root.model
                            }
                        }
                    }

                    Item {
                        Layout.minimumWidth: 8
                        Layout.fillWidth: true
                    }

                    Row {
                        id: buttonsRow
                        Layout.alignment: Qt.AlignTop | Qt.AlignRight
                        spacing: 8

                        Button {
                            hoverEnabled: true
                            ToolTip.visible: hovered
                            ToolTip.delay: 1000
                            ToolTip.text: "Save changes\n" + action.shortcut

                            action: Action {
                                text: "Save"
                                shortcut: "Ctrl+S"
                                enabled: root.model.has_changes
                                onTriggered: root.model.save_changes()
                            }
                        }

                        Button {
                            hoverEnabled: true
                            ToolTip.visible: hovered
                            ToolTip.delay: 1000
                            ToolTip.text: "Revert changes\n" + action.shortcut

                            action: Action {
                                text: "Revert"
                                shortcut: "Ctrl+R"
                                enabled: root.model.has_changes
                                onTriggered: root.model.revert_changes()
                            }
                        }
                    }
                }

                StackLayout {
                    id: panelsStack
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.leftMargin: 8
                    Layout.rightMargin: 8
                    Layout.bottomMargin: 8
                    currentIndex: root.maximized ? 1 : 0
                    property int panelMaxHeight: mainStack.height - profileRow.height - 24

                    RowLayout {
                        Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
                        uniformCellSizes: true
                        spacing: 8

                        Repeater {
                            model: 4

                            PanelView {
                                required property int index
                                Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
                                Layout.fillWidth: true
                                Layout.maximumHeight: panelsStack.panelMaxHeight
                                panel: root.model.panels[index]
                                isMaximized: root.maximized
                                isFocused: root.focusedPanel == index

                                onFocused: root.focusedPanel = index

                                onMaximized: {
                                    root.focusedPanel = index;
                                    root.maximized = true;
                                }
                            }
                        }
                    }

                    StackLayout {
                        currentIndex: root.focusedPanel

                        Repeater {
                            model: 4
                            PanelView {
                                required property int index
                                Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
                                Layout.fillWidth: true
                                Layout.maximumHeight: panelsStack.panelMaxHeight
                                panel: root.model.panels[index]
                                isMaximized: root.maximized
                                isFocused: root.focusedPanel == index

                                onUnmaximized: root.maximized = false
                            }
                        }
                    }
                }
            }
        }
    }
}
