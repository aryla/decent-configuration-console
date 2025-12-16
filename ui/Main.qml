import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Model

ApplicationWindow {
    id: root
    width: 960
    height: 540
    visible: true
    title: "Decent Configuration Console"

    property Model model

    header: ToolBar {
        topPadding: 8
        bottomPadding: 8

        RowLayout {
            anchors.fill: parent

            Text {
                visible: root.model.connected
                text: "Pad: "
            }
            Button {
                visible: root.model.connected
                text: root.model.alias
                font.family: "monospace"
                onClicked: padInfo.open()

                Popup {
                    id: padInfo
                    modal: true
                    focus: true
                    topPadding: 16
                    bottomPadding: 16
                    leftPadding: 16
                    rightPadding: 16
                    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

                    Component.onCompleted: {
                        root.model.connected_changed.connect(function () {
                            if (!root.model.connected) {
                                padInfo.close();
                            }
                        });
                    }

                    GridLayout {
                        columns: 2

                        Text {
                            text: "Serial number: "
                        }

                        Text {
                            text: root.model.serial
                            font.family: "monospace"
                        }

                        Text {
                            text: "Alias: "
                        }

                        TextField {
                            Layout.fillWidth: true
                            text: root.model.alias
                            maximumLength: 30
                            font.family: "monospace"
                            onEditingFinished: root.model.alias = text
                        }

                        Text {
                            text: "Mode: "
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
                    }
                }
            }

            Item {
                Layout.fillWidth: true
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

            Button {
                text: "Quit"
                onClicked: root.close()
            }
        }
    }

    footer: ToolBar {
        Text {
            Layout.alignment: Qt.AlignVCenter | Qt.AlignLeft
            text: root.model.message
        }
    }

    StackLayout {
        anchors.fill: parent
        currentIndex: root.model.connected ? 1 : 0

        Item {
            ColumnLayout {
                anchors.centerIn: parent

                Text {
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

        ColumnLayout {
            spacing: 8

            RowLayout {
                Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
                Layout.fillWidth: true
                Layout.topMargin: 8
                Layout.leftMargin: 8
                Layout.rightMargin: 8

                spacing: 16

                Item {
                    Layout.fillWidth: true
                    Layout.horizontalStretchFactor: 1089
                }

                ProfileView {
                    profileId: 0
                    model: root.model
                }

                ProfileView {
                    profileId: 1
                    model: root.model
                }

                ProfileView {
                    profileId: 2
                    model: root.model
                }

                ProfileView {
                    profileId: 3
                    model: root.model
                }

                Item {
                    Layout.fillWidth: true
                    Layout.horizontalStretchFactor: 868
                }

                Button {
                    action: Action {
                        text: "Save"
                        shortcut: "Ctrl+S"
                        enabled: root.model.has_changes
                        onTriggered: root.model.save_changes()
                    }
                }

                Button {
                    action: Action {
                        text: "Revert"
                        shortcut: "Ctrl+Z"
                        enabled: root.model.has_changes
                        onTriggered: root.model.revert_changes()
                    }
                }
            }

            RowLayout {
                Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
                uniformCellSizes: true
                spacing: 8

                PanelView {
                    Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    panel: root.model.panel0
                }

                PanelView {
                    Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    panel: root.model.panel1
                }

                PanelView {
                    Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    panel: root.model.panel2
                }

                PanelView {
                    Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    panel: root.model.panel3
                }
            }
        }
    }
}
