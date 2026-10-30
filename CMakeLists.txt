# Hunter: The Reckoning (original Xbox), statically recompiled

cmake_minimum_required(VERSION 3.25)
project(hunter LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# the SDK: sdk/ here, two folders up inside the SDK's templates, a checkout beside this repository, else downloaded
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/sdk/cmake/XbeRecomp.cmake)
    set(SDK ${CMAKE_CURRENT_SOURCE_DIR}/sdk)
elseif(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/../../cmake/XbeRecomp.cmake)
    set(SDK ${CMAKE_CURRENT_SOURCE_DIR}/../..)
elseif(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/../XboxXBE-Recomp/cmake/XbeRecomp.cmake)
    set(SDK ${CMAKE_CURRENT_SOURCE_DIR}/../XboxXBE-Recomp)
else()
    include(FetchContent)
    # the commit sdk.toml pins
    FetchContent_Declare(xbe_sdk GIT_REPOSITORY https://github.com/TGP482/XboxXBE-Recomp.git
                         GIT_TAG 91146ff6e2a218b19c1109dc665d06020472ab57)
    FetchContent_MakeAvailable(xbe_sdk)
    set(SDK ${xbe_sdk_SOURCE_DIR})
endif()
include(${SDK}/cmake/XbeRecomp.cmake)

file(GLOB XBE_HOST_SOURCES CONFIGURE_DEPENDS src/*/*.cpp)
list(FILTER XBE_HOST_SOURCES EXCLUDE REGEX "/src/game/")

# partitions as xbe_symbols wrote them into config/game.toml
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS config/game.toml)
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/config/game.toml)
    file(STRINGS config/game.toml GAME_PARTITIONS REGEX "^partitions *=")
    string(REGEX MATCH "[0-9]+" GAME_PARTITIONS "${GAME_PARTITIONS}")
endif()
# no config yet: build.bat writes it with xbe_symbols, the change reconfigures
if(NOT GAME_PARTITIONS)
    set(GAME_PARTITIONS 8)
endif()

# target name = GAME_EXE in build.bat, xbe = GAME_XBE
add_xbe_image(Hunter default.xbe game.toml ${GAME_PARTITIONS} game)

# The XDK 4361 overlay (config/xdk/4361, included by config/game.toml) goes beside the config the first-launch
# compiler reads, so a release and a stale DLL rebuild find it; the SDK copies only config/*.toml.
add_custom_command(TARGET compiler_files POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_CURRENT_SOURCE_DIR}/config/xdk ${XBE_COMPILER_DIR}/config/xdk
    VERBATIM)
# the recompile step depends on config/*.toml only: after editing the overlay, touch config/game.toml

# The executable takes its code DLL for current only when the DLL is newer (sdk/runtime/app/game_code.cpp). A
# change to host code alone relinks the executable and leaves the DLL as it was, which would then be rebuilt at
# the next start: mark the existing DLL current again. Ninja still relinks it when its own inputs change.
add_custom_command(TARGET Hunter POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E touch_nocreate $<TARGET_FILE_DIR:Hunter>/Hunter.dll
    VERBATIM)
