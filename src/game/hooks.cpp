// Hooks for default.xbe. A strong definition replaces the recompiled function at that address, for example:
//
// #include "xdk/hle.h"
//
// X86_EXTERN_FUNC(__imp__sub_00012345);
// X86_FUNC(sub_00012345) {
//     __imp__sub_00012345(ctx, base);  // the original
// }
//
// None yet. The SDK implements all 123 of this XBE's kernel imports, DbgPrint (ordinal 8) in
// sdk/runtime/kernel/xboxkrnl.cpp.
#include "xdk/hle.h"
