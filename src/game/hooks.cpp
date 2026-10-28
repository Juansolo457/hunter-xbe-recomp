// Hooks for default.xbe. A strong definition replaces the recompiled function at that address, for example:
//
// #include "xdk/hle.h"
//
// X86_EXTERN_FUNC(__imp__sub_00012345);
// X86_FUNC(sub_00012345) {
//     __imp__sub_00012345(ctx, base);  // the original
// }
#include "core/log.h"
#include "kernel/exports.h"
#include "xdk/hle.h"

// cdecl, the one kernel import of this XBE the SDK does not define (the XDK libraries' debug messages)
KERNEL_EXPORT(8, DbgPrint, 0) {
    LOGI("DbgPrint: %s", static_cast<const char*>(kernel::HostPtr(a[0])));
    return 0;
}
