# Melee-Pseudocode
Pseudocode reconstruction of the Smash Bros Melee assembly code.

Each function is formatted like this:
```
fn func_name@0x01234ABCD(Type argName@register, ...) -> ReturnType@register or void
@Notes:
  # optional notes, for example 'This function is only called by XYZ'.
@Reimplementation:
  # only if deemed useful to make it easier to understand the function.
@AssemblyPseudocode:
  # Pseudocode somewhat close to the assembly code.
  # Examples:
  #
  # float velocity@f1 = 5
  # Declares a float value velocity with storage in register f1 and value 5.
  # 
  # pCharData@r31.ledgeGrabCooldown(int)@0x2064
  # Accesses a struct member: pCharData pointer with storage in r31 is dereferenced
  # with an offset of 0x2064 to get the ledgeGrabCooldown member. The optional (int)
  # type is sometimes used when the datatype size or type is not obvious.
  # 
  # TOC is used to refer to the "Table of Contents" pointer, which is always
  # stored in register r2. Expressions like TOC.float@-0x778C refer to the float at
  # r2-0x778C (which is 0.0f). Constants are usually accesed via TOC in the assembly.
  #
  # Global variables are usually accessed via the constant register r13.
  # For example p_stc_ftcommon@(r13-0x514c) refers to a struct that is documented in the
  # m-Ex project, see here:
  # https://github.com/akaneia/m-ex/blob/master/MexTK/include/fighter.h
  #
  # Stack storage is denoted as 'variable@sp0x34', which means that the variable is
  # stored at r1+0x34, where r1 is the stack pointer.
  #
  # The code is sometimes sprinkled with commends that start with #abcd0123,
  # that means that the following code starts at that address in the assembly code.
  # This is useful for setting breakpoints, or for double checking that the pseudocode
  # is really correct.
@Assembly:
  # The ASM instructions.
  # Sometimes still interleaved with auto generated Pseudocode instructions,
  # but that's only an artifact of the translation process.
```
There are a few versions of a community spreadsheet floating around, where struct datatypes,
addresses of global values, and other things are documented. I use this one, which is editable:
https://docs.google.com/spreadsheets/d/1JX2w-r2fuvWuNgGb6D3Cs4wHQKLFegZe2jhbBuIhCG8/edit#gid=12

There are also multiple symbol maps floating around. Symbol maps map function/symbol names to
address ranges in the assembly code, so that names can be assigned to the assembly functions.
They can be used in the Dolphin Emulator in debug mode. I use this one:
https://github.com/UnclePunch/Training-Mode/blob/master/GTME01.map
