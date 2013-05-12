include ../global.properties
include ../project.properties

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


SUBDIRS = include

.PHONY: clean cleanall upload install install-dir install-tar $(SUBDIRS)

subdirs: $(SUBDIRS)

$(SUBDIRS):
	$(MAKE) -C $@

all: 	subdirs $(TARGET)

$(TARGET): $(OBJS) Makefile
	$(CC) $(OFLAGS) $(OBJS) -o $@

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

install-tar:
	tar -czf $(TAR) $(TARGET) $(SCRIPTS)


# include the dependencies in all .d files
-include $(DEPS)

