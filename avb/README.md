# Original firmware descriptors required by athens ABL

`oem_boot_descriptors.img` is a 704-byte unsigned AVB metadata container holding
only the original hash descriptors for `pvmfw` and `countrycode`, copied from
stock OS4.0.6.0.XPICNXM vbmeta. It contains no firmware payload and is never
flashed as a partition image. The ROM build includes its descriptors in the
signed top-level vbmeta.

The bootloader requests boot, dtbo, vendor_boot, init_boot, pvmfw and countrycode.
Removing the last two descriptors causes ABL to reject the slot with:
`num of loaded partitions 4, requested 6`.

Keep pvmfw and countrycode outside AB_OTA_PARTITIONS. This configuration uses
their existing stock contents. The descriptors were checked against the OS4
partition images when generating this container.
Disabling Android protected VM support does not remove ABL's request for pvmfw.

Descriptor image sizes: pvmfw 761856 bytes; countrycode 32 bytes. Both are
SHA-256 descriptors with A/B suffix handling enabled. For another firmware
baseline, verify the preserved partitions against these descriptors before use.
