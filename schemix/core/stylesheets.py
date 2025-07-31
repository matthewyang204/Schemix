qdockwidget_sub_chap = """
        QDockWidget {
            background-color: #4caf50;
            border: 1px solid #ccc;
            titlebar-close-icon: url(close.svg);
            titlebar-normal-icon: url(restore.svg);
        }

        QDockWidget::title {
            background-color: #1b1b1b;
            padding: 6px;
            font-weight: bold;
            font-size: 14px;
            border-bottom: 1px solid #bbb;
        }

        QListWidget {
            background-color: #1b1b1b;
            border: none;
            padding: 4px;
            font-size: 13px;
            selection-background-color: #d0ebff;
            selection-color: black;
        }

        QListWidget::item {
            padding: 6px;
            margin-bottom: 2px;
            border-radius: 4px;
        }

        QListWidget::item:selected {
            background-color: #a8d8ff;
            color: black;
        }

        QPushButton {
            background-color: #4caf50;
            color: white;
            padding: 6px 12px;
            font-size: 13px;
            font-weight: bold;
            border: none;
            border-radius: 6px;
        }

        QPushButton:hover {
            background-color: #45a049;
        }

        QPushButton:pressed {
            background-color: #388e3c;
        }
        """
