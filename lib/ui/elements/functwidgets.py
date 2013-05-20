#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import logging

import gtk, pango

class PlatformSlotSetupWidget(gtk.Frame):

    buttongroup_apply_all = None

    def __init__(self, platform_slot_adapter, product_selection_widget):
        super(PlatformSlotSetupWidget, self).__init__("Nonce")
        self.platform_slot_adapter = platform_slot_adapter
        self.platform_slot_adapter.connect('on-changed', self.__update)

        self.product_selection_widget = product_selection_widget
        product_selection_widget.set_isready_cb(self.__product_selection_isready_cb)

        self._init_visuals()

    def __update(self, adapter):
        pass

    def __product_selection_isready_cb(self, is_ready, adapter):
        if is_ready:
            self.uut_setup_frame.show()
        else:
            self.uut_setup_frame.hide()

    def _init_visuals(self):
        
        self.set_label("Slot [%s]" % self.platform_slot_adapter.address[1])
        self.set_label_align(0.5, 0.5)

        # - - - - - - - - - - - - - - -
        # create Frame and Box structure
        #
        self.hbox = {}
        self.vbox = {}

        self.hbox["top"] = gtk.HBox(False, 0)
        self.add(self.hbox["top"])

        label = gtk.Label("")
        label.set_markup("<u>UUT Setup</u>")
        self.uut_setup_frame = gtk.Frame()
        self.uut_setup_frame.set_label_widget(label)
        self.uut_setup_frame.set_property('shadow-type', gtk.SHADOW_NONE)

        label = gtk.Label("")
        label.set_markup("<u>Product/Test Setup</u>")
        self.product_setup_frame = gtk.Frame()
        self.product_setup_frame.set_label_widget(label)
        self.product_setup_frame.set_property('shadow-type', gtk.SHADOW_NONE)

        self.hbox["top"].pack_start(self.product_setup_frame)
        self.hbox["top"].pack_start(self.uut_setup_frame)

        self.vbox["right"] = gtk.VBox(False, 0)
        align = gtk.Alignment(.5, .5)
        align.add(self.vbox["right"])
        self.product_setup_frame.add(align)

        self.vbox["left"] = gtk.VBox(False, 0)
        align = gtk.Alignment(.5, .5)
        align.add(self.vbox["left"])
        self.uut_setup_frame.add(align)
        self.uut_setup_frame.hide()

        self.buttonbox_applytoall = gtk.VButtonBox()
        self.buttonbox_applytoall.set_layout(gtk.BUTTONBOX_SPREAD)
        self.hbox["right_inner"] = gtk.HBox(False, 0)

        self.vbox["right"].pack_start(self.buttonbox_applytoall, False, False,
                10)
        self.vbox["right"].pack_start(gtk.HSeparator(), False, False, 10)
        self.vbox["right"].pack_start(self.hbox["right_inner"], False, False,
                10)

        self.vbox["right_innerleft"] = gtk.VBox(False, 0)
        self.vbox["right_innerright"] = gtk.VBox(False, 0)
        self.hbox["right_inner"].pack_start(self.vbox["right_innerleft"], False,
                False, 10)

        self.hbox["right_inner"].pack_start(self.product_selection_widget, False,
                False, 10)

        # - - - - - - - - - - - - - - -
        # create checkboxes, radio buttons, and button group
        #
        self.checkbox = {}

        self.radiobutton_apply_all = gtk.RadioButton(
                self.buttongroup_apply_all, "Apply to All", False )
        self.radiobutton_apply_all.set_active(False)
        self.buttongroup_apply_all = self.radiobutton_apply_all
        self.buttonbox_applytoall.pack_start(self.radiobutton_apply_all)

        self.checkbox["program_bootloader"] = gtk.CheckButton(
                "Program MAC/Bootloader", False )
        self.checkbox["run_nfs_test"] = gtk.CheckButton(
                "Run NFS Test", False )
        self.checkbox["load_kfs"] = gtk.CheckButton(
                "Load Kernel & Filesystem", False )
        self.checkbox["first_boot"] = gtk.CheckButton(
                "First Boot", False )
        for key in ["program_bootloader", "run_nfs_test", "load_kfs", "first_boot"]:
            self.vbox["right_innerright"].pack_start(self.checkbox[key])

        # - - - - - - - - - - - - - - -
        # create comboboxes and text entry boxes
        #
        self.text_inputs = {}
        try:
            module_dotted_path = "emac.ui.elements.widgets"
            module = __import__(module_dotted_path, fromlist = ["uut_setup"] )
            uut_widget_module = getattr(module, "uut_setup")
        except AttributeError:
            sys.exit("ERROR: not found: {0}".format(module_dotted_path))

        self.uut_setup_widget = uut_widget_module.UUTSelectionWidget(
                self.platform_slot_adapter)
        self.vbox["left"].pack_start(self.uut_setup_widget)

        self.show_all()
        self.product_setup_frame.show()
        self.uut_setup_frame.hide()

class AbstractSelectionWidget(gtk.VBox):

    def __init__(self, initial_data, cb, is_ready_cb=None, adapter=None):
        super(AbstractSelectionWidget, self).__init__(False, 10)
        self.labeled_combobox = list()

        self.adapter = adapter
        self.__is_ready_cb = is_ready_cb
        self.__setup_initial_combobox(initial_data, cb)

    def __setup_initial_combobox(self, initial_data, cb):
        label_markup, data = initial_data
        self.__create_combobox(label_markup)
        self.__populate_combobox(self.labeled_combobox[0][1].get_model(), data)
        handler_id = self.labeled_combobox[0][1].connect('changed',
                self.__combobox_changed_cb, cb)
        self.labeled_combobox[0][1].on_changed_handler_id = handler_id
        self.labeled_combobox[0][1].show()

    def set_isready_cb(self, cb):
        self.__is_ready_cb = cb

    def __is_ready(self, ready, adapter):
        if callable(self.__is_ready_cb):
            self.__is_ready_cb(ready, adapter)
            return True
        return False

    def __combobox_changed_cb(self, combobox, func):
        model = combobox.get_model()
        index = combobox.get_active()
        row = model[index]
        name = row[0]

        adapter = None
        if self.adapter:
            adapter = self.adapter
        result = func(name=name, adapter=adapter)

        for row in self.labeled_combobox:
            if row[1] == combobox:
                break
        index = self.labeled_combobox.index(row)
        is_last_combobox = (len(self.labeled_combobox) == index + 1)

        if not isinstance(result, tuple):
            if is_last_combobox:
                return self.__is_ready(True, adapter)
        self.__is_ready(False, adapter)

        data, cb = result
        label_markup, data = data

        try:
            if not is_last_combobox:
                next_combobox = self.labeled_combobox[index + 1][1]
                next_combobox.disconnect(next_combobox.on_changed_handler_id)
                self.__populate_combobox(next_combobox.get_model(), data)
                next_combobox.set_active(-1)
                handler_id = next_combobox.connect('changed',
                        self.__combobox_changed_cb, cb)
                next_combobox.on_changed_handler_id = handler_id
                next_combobox.show()
                for row in self.labeled_combobox[index+2:]:
                    row[2].hide()
            else:
                self.__create_combobox(label_markup)
                new_combobox = self.labeled_combobox[index+1][1]
                self.__populate_combobox(new_combobox.get_model(), data)
                handler_id = new_combobox.connect('changed',
                        self.__combobox_changed_cb, cb)
                new_combobox.on_changed_handler_id = handler_id
                new_combobox.show()
        except ValueError:
            raise

    @staticmethod
    def __populate_combobox(model, data_list):
        model.clear()
        for data in data_list:
            itr = model.append( (data["name"], data["shortdesc"] ) )

    def __create_combobox(self, label_markup=None):
        hbox = gtk.HBox(False, 0)
        hbox.show()

        label = gtk.Label("")
        hbox.pack_start(label)

        if label_markup:
            label.set_markup(label_markup)
            label.set_property('width-chars', 14)
            label.show()

        model = gtk.ListStore(str, str)
        combobox = gtk.ComboBox(model)
        combobox.set_property('width-request', 560)
        hbox.pack_start(combobox)

        column_name_cell = gtk.CellRendererText()
        column_name_cell.set_property('weight', 800)
        column_shortdesc_cell = gtk.CellRendererText()
        column_shortdesc_cell.set_property('xalign', 1.0) 
        column_shortdesc_cell.set_property('width-chars', 40)
        column_shortdesc_cell.set_property('ellipsize', pango.ELLIPSIZE_END)

        combobox.pack_start(column_name_cell, True)
        combobox.add_attribute(column_name_cell, 'text', 0)

        combobox.pack_start(column_shortdesc_cell, False)
        combobox.add_attribute(column_shortdesc_cell, 'text', 1)

        combobox.set_active(-1)
        combobox.show()

        self.pack_start(hbox)
        self.labeled_combobox.append((label, combobox, hbox))
