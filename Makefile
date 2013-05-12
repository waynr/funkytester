include current_test/project.properties

CFLAGS+=-I./include
TAR=$(TARGET).tar.gz

ifdef O
	ifeq ("$(origin O)", "command line")
		BUILD_DIR := $(O)
    		INSTALL_TARGET = install-dir
  	endif
else
  	INSTALL_TARGET = install-tar 
endif


OBJS=$(CFILES:.c=.o)
DEPS=$(OBJS:.o=.d)
GDB=$(TARGET).gdb

.PHONY: all clean cleanall upload install install-dir install-tar

all:	$(TARGET)

$(TARGET): $(OBJS) Makefile
	$(CC) $(OFLAGS) $(OBJS) -o ./bin/$@

%.o:	%.c
	$(CC) $(CFLAGS) -o $@ -c $<
	
clean:
	rm -f $(TARGET) $(DEPS) $(OBJS) $(GDB)

cleanall:
	rm -f $(TARGET) $(DEPS) $(OBJS) $(GDB)
	
upload: all
	$(WPUT) $(TARGET) ftp://$(LOGIN):$(PASSWORD)@$(TARGET_IP)/../../tmp/$(TARGET)

install: $(INSTALL_TARGET)

install-dir: install-tar
	tar -C $(BUILD_DIR) -xzf $(TAR)

install-nfs: install-tar
	sudo mkdir -p $(NFS_DIR)/root/$(TARGET_DIR)
	sudo tar -xzf $(TAR) -C $(NFS_DIR)/root/$(TARGET_DIR)
	sudo cp $(NFS_DIR)/root/$(TARGET_DIR)/$(NFS_INIT_SCRIPT) $(NFS_DIR)/etc/init.d/

install-tar: all
	tar -czf $(TAR) $(SCRIPTS) $(NFS_INIT_SCRIPT) 

mkubootimage: all
	mkubootimage $(UBSCRIPT) $(UBSCRIPT).img



# include the dependencies in all .d files
-include $(DEPS)

