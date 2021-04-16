Documentation on r13: "Reserved under 64-bit environment; not restored across system calls."
Seems to be used as a constant data segment pointer in Melee: r13 = 0x804db6a0

**Table of contents pointer rtoc = r2**
Historically (from IBM documentation) the set of pointers to a fragment's indirectly accessed data was referred to as the Table of Contents and its base register was called the Table of Contents Register (RTOC).
To access imported data or indirect global data, the build-time offset of the global data item is added to the value in GPR2. The result is the address of a pointer that points to the desired data.
To access imported routines, the offset of the routine is added to the value in GPR2, as in the data version, but the result points not directly to the routine, but to a transition vector.

Table of Contents pointer TOC = rtoc = r2 = 0x804df9e0 (for Melee, vanilla and slippi, never changes)
0x804DBcD4 = R2-0x3D0C: 0.5f (float)
0x804D8254 = R2-0x778C: 0.0f (float)
0x804D8330 = R2-0x76B0: 0.0f (float)
0x804d8334 = R2-0x76AC: 1.0f (float)
             R2-0x6B64: 1.0f (float) not tested if constant
             R2-0x6890: 0.0f (float)
             R2-0x7C30:  0.0f (float)
             R2-0x7C2C: -pi/2 (float), hex=0xbfc90fdb
             r2-0x7C28:    pi (float), hex=0x40490fdb
             r2-0x7C24:  0.0f (float)
             R2-0x7C20:  pi/2 (float), hex=0x3fc90fdb

# Static Variables
R13-0x514C: ftCommonData* p_stc_ftcommon
R13-0x5194: GXColor*      p_stc_shieldcolors
R13-0x6C98: int debugLevel?=0 # Probably always zero, meaning that debug tests are disabled. For example this disables a "position has NaN component" at the end of PlayerThink_Physics

# documented in community spreadsheed
struct PlayerEntityStruct:
	CharData* pCharData # offset = 0x2C

struct CharData:
	# members partially documented in the community spreadsheet, see 'Char Data Offsets' tab, under 'START Player Character Data'

################################################################################################
# Standard Math and Vector functions
################################################################################################

fn atan2@0x80022c30(y@f1, x@f2) -> angle@f1
@Notes:
	Mathematical definition:
	atan2(y,x) is the oriented angle in the range (-pi, pi]
	from the vector (1,0) to (x,y), or equivalently a=atan(y,x) is uniquely defined by the property
	(x,y)=(cos(a), sin(a)).
	
	Actual behaviour:
	Using the single precision (->bad approximation!) constants
	pi/2: hex = 0x3fc90fdb, or 0x3ff921fb60000000 when represented as a double,
	pi  : hex = 0x40490fdb, or 0x400921fb60000000 when represented as a double,
	the result is always in the range [-pi, pi]. The result is:
	x >  0: atan(y/x)
	x <  0, y >  0: atan(y/x) + pi
	x <  0, y <  0: atan(y/x) - pi
	x <  0, y == +0: +pi
	x <  0, y == -0: -pi
	x == 0, y > 0:  pi/2
	x == 0, y < 0: -pi/2
	x == 0, y == 0, signbit(x)!=signbit(y): pi/2
	x == 0, y == 0, signbit(x)==signbit(y): signbit set ? -pi/2 : pi/2
	All divisions, additions and subtractions above are done with single precision.
	Note how the result depends on the sign bit of y if x < 0 and y == 0.
@Reimplementation:
	bool sign_x = signbit(x)
	bool sign_y = signbit(y)
	if sign_x == sign_y:
		if sign_x != 0: # x, y <= 0
			return (x == 0) ? -pi/2 : atan(y/x)-pi
		else:
			return (x != 0) ? atan(y/x) : pi/2
	else:
		if x <  0: return atan(y/x) + pi
		if x != 0: return atan(y/x)
		return pi/2
@PseudoAssembly:
	# save lr, r1 on the stack
	float y@sp0x8 = y@f1
	float x@sp0xC = x@f2
	int raw_y@r0 = raw_cast(int) y@sp0x08
	int raw_x@r3 = raw_cast(int) x@sp0x0C
	bool sign_y@r4 = raw_y@r0.signbit # highest significant bit
	bool sign_x@r0 = raw_y@r3.signbit # highest significant bit
	#80022c54
	if sign_x@r0 == sign_y@r4:
		#80022c5c
		if sign_x@r0 != 0:
			x@f1 = x@sp0xC
			#80022c6c
			if x@f1 == 0: # 0 == *(float*)(r2-0x7C30)
				return -pi/2 # the hex value for -pi/2 is 0xbfc90fdb, stored at r2-0x7C2C
			y@f0 = y@sp0x8
			return atan@0x80022E68(f1 = y@f0 / x@f1) - pi # the hex value for pi is 0x40490fdb, stored at r2-0x7C28
		x@f1 = x@sp0xC
		#80022c98:
		if x@f1 != 0 # 0 == *(float*)(r2-0x7C24)
			y@f0 = y@sp0x8
			return atan@0x80022E68(f1 = y@f0 / x@f1)
		return pi/2 # the hex value for pi/2 is 0x3fc90fdb, stored at r2-0x7C20
	else: #80022cbc
		x@f1 = x@sp0xC
		#80022cc0
		if x@f1 < 0: # 0 == *(float*)(r2-0x7C24)
			return atan(f1 = y@sp0x8 / x@f1) + pi # the hex value for pi is 0x40490fdb, stored at r2-0x7C28
		if x@f1 != 0: # 0 == *(float*)(r2-0x7C24)
			return atan(f1 = y@sp0x8 / x@f1)
		return pi_half with sign of sign_y@r4 # hex value of pi_half: (16329 << 16) + 4049 = 0x3fc90fdb
	#80022d0c: restore stack and return
@Assembly:
	80022c30: mflr	r0
	80022c34: stw	r0, 0x0004 (sp)
	80022c38: stwu	sp, -0x0010 (sp)
	80022c3c: stfs	f1, 0x0008 (sp)
	80022c40: stfs	f2, 0x000C (sp)
	80022c44: lwz	r0, 0x0008 (sp)
	80022c48: lwz	r3, 0x000C (sp)
	80022c4c: rlwinm	r4, r0, 0, 0, 0 (80000000)
	80022c50: rlwinm	r0, r3, 0, 0, 0 (80000000)
	80022c54: cmpw	r0, r4
	80022c58: bne-	 ->0x80022CBC
	80022c5c: cmpwi	r0, 0
	80022c60: beq-	 ->0x80022C94
	80022c64: lfs	f0, -0x7C30 (rtoc)
	80022c68: lfs	f1, 0x000C (sp)
	80022c6c: fcmpu	cr0,f0,f1
	80022c70: bne-	 ->0x80022C7C
	80022c74: lfs	f1, -0x7C2C (rtoc)
	80022c78: b	->0x80022D0C
	80022c7c: lfs	f0, 0x0008 (sp)
	80022c80: fdivs	f1,f0,f1
	80022c84: bl	->0x80022E68
	80022c88: lfs	f0, -0x7C28 (rtoc)
	80022c8c: fsubs	f1,f1,f0
	80022c90: b	->0x80022D0C
	80022c94: lfs	f1, 0x000C (sp)
	80022c98: lfs	f0, -0x7C24 (rtoc)
	80022c9c: fcmpu	cr0,f1,f0
	80022ca0: beq-	 ->0x80022CB4
	80022ca4: lfs	f0, 0x0008 (sp)
	80022ca8: fdivs	f1,f0,f1
	80022cac: bl	->0x80022E68
	80022cb0: b	->0x80022D0C
	80022cb4: lfs	f1, -0x7C20 (rtoc)
	80022cb8: b	->0x80022D0C
	80022cbc: lfs	f1, 0x000C (sp)
	80022cc0: lfs	f0, -0x7C24 (rtoc)
	80022cc4: fcmpo	cr0,f1,f0
	80022cc8: bge-	 ->0x80022CE4
	80022ccc: lfs	f0, 0x0008 (sp)
	80022cd0: fdivs	f1,f0,f1
	80022cd4: bl	->0x80022E68
	80022cd8: lfs	f0, -0x7C28 (rtoc)
	80022cdc: fadds	f1,f0,f1
	80022ce0: b	->0x80022D0C
	80022ce4: fcmpu	cr0,f1,f0
	80022ce8: beq-	 ->0x80022CFC
	80022cec: lfs	f0, 0x0008 (sp)
	80022cf0: fdivs	f1,f0,f1
	80022cf4: bl	->0x80022E68
	80022cf8: b	->0x80022D0C
	80022cfc: addis	r3, r4, 16329
	80022d00: addi	r0, r3, 4059
	80022d04: stw	r0, 0x0008 (sp)
	80022d08: lfs	f1, 0x0008 (sp)
	80022d0c: lwz	r0, 0x0014 (sp)
	80022d10: addi	sp, sp, 16
	80022d14: mtlr	r0
	80022d18: blr

fn sin@0x803263d4(float angle@f1) -> result@f1
@Bug:
	For the angle 3.14159=atan2(0,-1), the result is
	sin( 3.14159) = -8.74228e-08 (0xbe7777a5c0000000). This wrong, the result should be positive because   0 < 3.14159  < Pi.
	sin(-3.14159) = +8.74228e-08 (0x3e7777a5c0000000). Also wrong, the result should be negative because -Pi < -3.14159 < 0.
	However for a slightly more accurate value of pi, the result is very accurate again.
	sin(3.141592, hex=0x400921f9f01b866e) = 2.7736e-06
	TODO: This makes me suspicious that a special case is used for the angle 3.13159=atan2(0,-1).

fn cos@0x80326240(float angle@f1) -> result@f1
@ExampleValues:
	cos(+-3.14159) = -1.0, where 3.14159=atan2(0,-1). The exact result is closer to -0.9999999999964793, but this is correctly
	rounded for single precision.

How these numerical errors affect vector normalization:
Sometimes vectors are normalized in a silly way:
When normalizing a 2D-vector v, a=atan2(v.y, v.x) is computed, then vec2(cos(a), sin(a)) is used as
the normalized vector, instead of just computing v/v.length().
When normalizing (-1,0) that way, we get a=atan2(0,-1)=3.14159, and then the result is vec2(-1, -8.74228e-08).
Similarly when normalizing (-1,-0), the result is vec2(-1, 8.74228e-08). TODO: research how exactly that is related
to the (extended) invisible ceiling glitch.

fn PSVECAdd@0x80342D54     (Vec3* pA@r3, Vec3* pB@r4, Vec3* pResult@r5): *pResult = *pA + *pB
fn PSVECSubtract@0x80342d78(Vec3* pA@r3, Vec3* pB@r4, Vec3* pResult@r5): *pResult = *pA - *pB

################################################################################################
# Animation state change functions?
################################################################################################

fn AS_Walk_Prefunction@0x800c9528(float argFloat@f1, PlayerEntityStruct* pPlayerEntityStruct@r3) -> ?:
@Notes:
	This function is called every time the walk speed transitions between slow/middle/fast,
	but not while the speed stays in one of those 3 states.
@Params:
	Example parameters for Peach:
	f1 = 0.0
	
	Example parameters for Falcon:
	f1 = 10.0
@PseudoAssembly:
	# save r29, ..., r31, f31 on the stackframe

	argFloat@f31 = argFloat@f1
	pPlayerEntityStruct@r29 = pPlayerEntityStruct@r3

	CharData* pCharData@r31 = pPlayerEntityStruct@r3.pCharData@0x2C

	float Multiplier@f8 = 1.0 # assuming TOC.float@-0x6B64 = 1.0 is const

	if pCharData@r31.MetalTextureByte@0x2223 & 0b01:
		# for peach this would be: r3 = 0x80c6d170 -> f8 = 0.7 (surrounded by many other float values)
		# on another dolphin instance r3 had another value, but still points to the same value 0.7
		# surrounded by those other values
		void* pData = r13-0x5184 # TODO: is this a struct, or just a pointer to a float? Is that float constant?
		Multiplier@f8 = *cast(float*)(pData+0) # always=0.7?

	if pCharData@r31.playerScale(float)@0x38 != 1.0 # assuming TOC.float@-0x6B64 = 1.0 is const
		Multiplier@f8 = AdjustSomething_DuetoModelScale_NotEqualOne@0x800CF594(f1 = Multiplier@f8, f2 = pCharData@r31.playerScale(float)@0x38, f3 = *(r13.float*@-0x517C)) # f3=1 for Peach

	if pCharData@r31.BunnyHood@0x197C != 0:
		Multiplier@f8 *= @r13.float@-0x5180

	# call AS_Walk: copy params to f1..f7, r4, r5
	f1 = argFloat@f31 # restore the f1 parameter, because f1 was used in between
	f2 = pCharData@r31.float@0x2DC # 70 for Peach, 54 for Falcon
	f3 = pCharData@r31.float@0x2E0 # 40 for Peach, 40 for Falcon
	f4 = pCharData@r31.float@0x2E4 # 30 for Peach, 25 for Falcon
	f5 = pCharData@r31.SlowWalkMax@0x011C # 0.187 for Peach (SlowWalkMax)
	f6 = pCharData@r31.MidWalkPoint@0x0120 # 0.47 for Peach (MidWalkPoint)
	f7 = pCharData@r31.FastWalkMin@0x0124 # 0.76 for Peach (FastWalkMin)
	r3 = pPlayerEntityStruct@r29 # restore the r3 parameter, because r3 was used in between
	r4 = 15 
	r5 = 0
	Call(0x800DFCA4="AS_Walk ...")
@Assembly:
	#800c9528: mflr	r0
	r0 = lr
	#800c952c: stw	r0, 0x0004 (sp)
	*(r1 + 0x0004) = r0
	#800c9530: stwu	sp, -0x0030 (sp)
	*(r1 + -0x0030) = r1
	r1 += -0x0030
	#800c9534: stfd	f31, 0x0028 (sp)
	*(double*)(r1 + 0x0028) = f31
	#800c9538: fmr	f31, f1
	f31 = f1
	#800c953c: stw	r31, 0x0024 (sp)
	*(r1 + 0x0024) = r31
	#800c9540: stw	r30, 0x0020 (sp)
	*(r1 + 0x0020) = r30
	#800c9544: stw	r29, 0x001C (sp)
	*(r1 + 0x001C) = r29
	#800c9548: mr	r29, r3
	r29 = r3
	#800c954c: lwz	r31, 0x002C (r3)
	r31 = *(r3 + 0x002C)
	#800c9550: lfs	f8, -0x6B64 (rtoc)
	f8 = *(float*)(r2 + -0x6B64)
	#800c9554: lbz	r0, 0x2223 (r31)
	r0 = *(byte*)(r31 + 0x2223)
	#800c9558: addi	r30, r31, 732
	r30 = r31 + 732 
	#800c955c: rlwinm.	r0, r0, 0, 31, 31 (00000001)
	r0 = r0 & 0b10000000000000000000000000000000
	@CR0 = compare_signed(r0, 0)
	#800c9560: beq-	 ->0x800C956C
	if CR[0] reflects 'eq': goto ->0x800C956C
	#800c9564: lwz	r3, -0x5184 (r13)
	r3 = *(r13 + -0x5184)
	#800c9568: lfs	f8, 0 (r3)
	f8 = *(float*)(r3 + 0)
	#800c956c: lfs	f0, -0x6B64 (rtoc)
	f0 = *(float*)(r2 + -0x6B64)
	#800c9570: lfs	f2, 0x0038 (r31)
	f2 = *(float*)(r31 + 0x0038)
	#800c9574: fcmpu	cr0,f0,f2
	cr0 = compare_floats(f0, f2) # a<b: 0b1000, a>b: 0b0100, a==b: 0b0010, unordered(NaN): 0b0001
	@FPCC = cr0
	if one operand is SNaN: @VXSNAN = 1
	#800c9578: beq-	 ->0x800C9590
	if CR[0] reflects 'eq': goto ->0x800C9590
	#800c957c: lwz	r3, -0x517C (r13)
	r3 = *(r13 + -0x517C)
	#800c9580: fmr	f1, f8
	f1 = f8
	#800c9584: lfs	f3, 0x000C (r3)
	f3 = *(float*)(r3 + 0x000C)
	#800c9588: bl	->0x800CF594
	LR = __next_instruction_address
	goto ->0x800CF594
	#800c958c: fmr	f8, f1
	f8 = f1
	#800c9590: lwz	r0, 0x197C (r31)
	r0 = *(r31 + 0x197C)
	#800c9594: cmplwi	r0, 0
	CR0 = compare_unsigned(r0, 0) # a<b: 0b1000, a>b: 0b0100, a==b: 0b0010; last bit is set to the summary overflow bit from @XER
	#800c9598: beq-	 ->0x800C95A8
	if CR[0] reflects 'eq': goto ->0x800C95A8
	#800c959c: lwz	r3, -0x5180 (r13)
	r3 = *(r13 + -0x5180)
	#800c95a0: lfs	f0, 0 (r3)
	f0 = *(float*)(r3 + 0)
	#800c95a4: fmuls	f8,f8,f0
	f8 = f8 * f0 (as singles)
	#800c95a8: fmr	f1, f31
	f1 = f31
	#800c95ac: lfs	f2, 0 (r30)
	f2 = *(float*)(r30 + 0)
	#800c95b0: lfs	f3, 0x0004 (r30)
	f3 = *(float*)(r30 + 0x0004)
	#800c95b4: mr	r3, r29
	r3 = r29
	#800c95b8: lfs	f4, 0x0008 (r30)
	f4 = *(float*)(r30 + 0x0008)
	#800c95bc: lfs	f5, 0x011C (r31)
	f5 = *(float*)(r31 + 0x011C)
	#800c95c0: li	r4, 15
	r4 = 0 + 15 
	#800c95c4: lfs	f6, 0x0120 (r31)
	f6 = *(float*)(r31 + 0x0120)
	#800c95c8: li	r5, 0
	r5 = 0 + 0 
	#800c95cc: lfs	f7, 0x0124 (r31)
	f7 = *(float*)(r31 + 0x0124)
	#800c95d0: bl	->0x800DFCA4
	LR = __next_instruction_address
	goto ->0x800DFCA4
	#800c95d4: lwz	r0, 0x0034 (sp)
	r0 = *(r1 + 0x0034)
	#800c95d8: lfd	f31, 0x0028 (sp)
	f31 = *(double*)(r1 + 0x0028)
	#800c95dc: lwz	r31, 0x0024 (sp)
	r31 = *(r1 + 0x0024)
	#800c95e0: lwz	r30, 0x0020 (sp)
	r30 = *(r1 + 0x0020)
	#800c95e4: lwz	r29, 0x001C (sp)
	r29 = *(r1 + 0x001C)
	#800c95e8: addi	sp, sp, 48
	sp = r1 + 48 
	#800c95ec: mtlr	r0
	lr = r0
	#800c95f0: blr
	goto LR

fn AS_Walk(PlayerEntityStruct* pPlayerEntityStruct@r3,
           int unkIntParam1?@r4, # always = 15 when called from AS_Walk_Prefunction
           int unkIntParam2?@r5, # always = 0  when called from AS_Walk_Prefunction
           float unkFloatParam@f1, # same param as in AS_Walk_Prefunction
           float SlowWalkAnimLength@f2, float WalkAnimLength@f3, float FastWalkAnimLength@f4,
           float SlowWalkSpeed@f5, WalkSpeed@f6, float FastWalkSpeed@f7,
           float Multiplier?@f8) -> ?
@Notes:
	This function is called every time the walk speed transitions between slow/middle/fast,
	but not while the speed stays in one of those 3 states.
@PseudoAssembly:
	# save r29, ..., r31, f26, ..., f31 on the stackframe
	
	# duplicate some registers so we can overwrite and later restore them
	f31 = FastWalkSpeed@f7
	f30 = WalkSpeed@f6
	f29 = SlowWalkSpeed@f5
	f28 = FastWalkAnimLength@f4
	f27 = WalkAnimLength@f3
	f26 = SlowWalkAnimLength@f2
	r30 = unkIntParam1@r4
	r29 = pPlayerEntityStruct@r3
	
	pCharData@r31 = pPlayerEntityStruct@r3.pCharData@0x2C
	pCharData@r31.float@0x2360 = Multiplier@f8
	pCharData@r3 = pPlayerEntityStruct@r3.pCharData@0x2C # unnecessary memory read, could just do r3=r31
	float absGroundVel@f2 = pCharData@r3.groundVel@0xEC
	if absGroundVel@f2 < 0: # 0.0f@(r2-0x6890)
		absGroundVel@f2 = -absGroundVel@f2
	f3 = pCharData@r3.float@0x2360 # TODO: undocumented member
	float walkMaxVel@f4 = pCharData@r3.WalkMaxVel@0x0118
	global ftCommonData* p_stc_ftcommon@r4 = p_stc_ftcommon@(r13-0x514C)
	if absGroundVel@f2 == ftCommonData@r4.float@0x2C * f3 * walkMaxVel@f4:
		r0 = 2 
	else:
		r0 = (absGroundVel@f2 >= ftCommonData@r4.float@0x28 * f3 * walkMaxVel@f4) ? 1 : 0
	ActionStateChange@0x800693AC(r3 = r29, r4 = r30 + r0, r6 = 0, f1=unkFloatParam@f1, f2 = TOC.float@-0x688C, f3 = 0 /*=TOC.float@-0x6890*/) # possibly more float parameters are used.
	AS_AnimationFrameUpdate&More@0x8006EBA4(r3 = r29)
	
	# TODO: look what the following character data fields are. Just a copy of other fields?
	pCharData@r31.float?@0x2340 = pCharData@r31.groundVel@0xEC
	pCharData@r31.int?@0x2344   = unkIntParam1@r30
	pCharData@r31.float?@0x2348 = SlowWalkAnimLength@f26
	pCharData@r31.float?@0x234C = WalkAnimLength@f27
	pCharData@r31.float?@0x2350 = FastWalkAnimLength@f28
	pCharData@r31.float?@0x2354 = SlowWalkSpeed@f29
	pCharData@r31.float?@0x2358 = WalkSpeed@f30
	pCharData@r31.float?@0x235C = FastWalkSpeed@f31
	# unwind stackframe and return
@Assembly:
	#800dfca4: mflr	r0
	r0 = lr
	#800dfca8: stw	r0, 0x0004 (sp)
	*(r1 + 0x0004) = r0
	#800dfcac: stwu	sp, -0x0098 (sp)
	*(r1 + -0x0098) = r1
	r1 += -0x0098
	#800dfcb0: stfd	f31, 0x0090 (sp)
	*(double*)(r1 + 0x0090) = f31
	#800dfcb4: fmr	f31, f7
	f31 = f7
	#800dfcb8: stfd	f30, 0x0088 (sp)
	*(double*)(r1 + 0x0088) = f30
	#800dfcbc: fmr	f30, f6
	f30 = f6
	#800dfcc0: stfd	f29, 0x0080 (sp)
	*(double*)(r1 + 0x0080) = f29
	#800dfcc4: fmr	f29, f5
	f29 = f5
	#800dfcc8: stfd	f28, 0x0078 (sp)
	*(double*)(r1 + 0x0078) = f28
	#800dfccc: fmr	f28, f4
	f28 = f4
	#800dfcd0: stfd	f27, 0x0070 (sp)
	*(double*)(r1 + 0x0070) = f27
	#800dfcd4: fmr	f27, f3
	f27 = f3
	#800dfcd8: stfd	f26, 0x0068 (sp)
	*(double*)(r1 + 0x0068) = f26
	#800dfcdc: fmr	f26, f2
	f26 = f2
	#800dfce0: stw	r31, 0x0064 (sp)
	*(r1 + 0x0064) = r31
	#800dfce4: stw	r30, 0x0060 (sp)
	*(r1 + 0x0060) = r30
	#800dfce8: mr	r30, r4
	r30 = r4
	#800dfcec: stw	r29, 0x005C (sp)
	*(r1 + 0x005C) = r29
	#800dfcf0: mr	r29, r3
	r29 = r3
	#800dfcf4: lwz	r31, 0x002C (r3)
	r31 = *(r3 + 0x002C)
	#800dfcf8: stfs	f8, 0x2360 (r31)
	*(float*)(r31 + 0x2360) = f8
	#800dfcfc: lwz	r3, 0x002C (r3)
	r3 = *(r3 + 0x002C)
	#800dfd00: lfs	f0, -0x6890 (rtoc)
	f0 = *(float*)(r2 + -0x6890)
	#800dfd04: lfs	f2, 0x00EC (r3)
	f2 = *(float*)(r3 + 0x00EC)
	#800dfd08: fcmpo	cr0,f2,f0
	cr0 = compare_floats(f2, f0) # a<b: 0b1000, a>b: 0b0100, a==b: 0b0010, unordered(NaN): 0b0001
	@FPCC = cr0
	if one operand is SNaN: { @VXSNAN = 1; if @VE == 0: @VXVC = 1; }
	elif one operand is QNaN: @VXVC = 1
	#800dfd0c: bge-	 ->0x800DFD14
	if CR[0] reflects 'ge': goto ->0x800DFD14
	#800dfd10: fneg	f2,f2
	f2 = -f2 # sign bit is flipped, even for NaN values
	#800dfd14: lwz	r4, -0x514C (r13)
	r4 = *(r13 + -0x514C)
	#800dfd18: lfs	f4, 0x0118 (r3)
	f4 = *(float*)(r3 + 0x0118)
	#800dfd1c: lfs	f0, 0x002C (r4)
	f0 = *(float*)(r4 + 0x002C)
	#800dfd20: lfs	f3, 0x2360 (r3)
	f3 = *(float*)(r3 + 0x2360)
	#800dfd24: fmuls	f0,f0,f4
	f0 = f0 * f4 (as singles)
	#800dfd28: fmuls	f0,f3,f0
	f0 = f3 * f0 (as singles)
	#800dfd2c: fcmpo	cr0,f2,f0
	cr0 = compare_floats(f2, f0) # a<b: 0b1000, a>b: 0b0100, a==b: 0b0010, unordered(NaN): 0b0001
	@FPCC = cr0
	if one operand is SNaN: { @VXSNAN = 1; if @VE == 0: @VXVC = 1; }
	elif one operand is QNaN: @VXVC = 1
	#800dfd30: cror	2, 1, 2
	CR.bits[2] = CR.bits[1] or CR.bits[2]
	#800dfd34: bne-	 ->0x800DFD40
	if CR[0] reflects 'ne': goto ->0x800DFD40
	#800dfd38: li	r0, 2
	r0 = 0 + 2 
	#800dfd3c: b	->0x800DFD64
	goto ->0x800DFD64
	#800dfd40: lfs	f0, 0x0028 (r4)
	f0 = *(float*)(r4 + 0x0028)
	#800dfd44: fmuls	f0,f0,f4
	f0 = f0 * f4 (as singles)
	#800dfd48: fmuls	f0,f3,f0
	f0 = f3 * f0 (as singles)
	#800dfd4c: fcmpo	cr0,f2,f0
	cr0 = compare_floats(f2, f0) # a<b: 0b1000, a>b: 0b0100, a==b: 0b0010, unordered(NaN): 0b0001
	@FPCC = cr0
	if one operand is SNaN: { @VXSNAN = 1; if @VE == 0: @VXVC = 1; }
	elif one operand is QNaN: @VXVC = 1
	#800dfd50: cror	2, 1, 2
	CR.bits[2] = CR.bits[1] or CR.bits[2]
	#800dfd54: bne-	 ->0x800DFD60
	if CR[0] reflects 'ne': goto ->0x800DFD60
	#800dfd58: li	r0, 1
	r0 = 0 + 1 
	#800dfd5c: b	->0x800DFD64
	goto ->0x800DFD64
	#800dfd60: li	r0, 0
	r0 = 0 + 0 
	#800dfd64: lfs	f2, -0x688C (rtoc)
	f2 = *(float*)(r2 + -0x688C)
	#800dfd68: add	r4, r30, r0
	r4 = r30 + r0 
	#800dfd6c: lfs	f3, -0x6890 (rtoc)
	f3 = *(float*)(r2 + -0x6890)
	#800dfd70: mr	r3, r29
	r3 = r29
	#800dfd74: li	r6, 0
	r6 = 0 + 0 
	#800dfd78: bl	->0x800693AC
	LR = __next_instruction_address
	goto ->0x800693AC
	#800dfd7c: mr	r3, r29
	r3 = r29
	#800dfd80: bl	->0x8006EBA4
	LR = __next_instruction_address
	goto ->0x8006EBA4
	#800dfd84: lfs	f0, 0x00EC (r31)
	f0 = *(float*)(r31 + 0x00EC)
	#800dfd88: stfs	f0, 0x2340 (r31)
	*(float*)(r31 + 0x2340) = f0
	#800dfd8c: stw	r30, 0x2344 (r31)
	*(r31 + 0x2344) = r30
	#800dfd90: stfs	f26, 0x2348 (r31)
	*(float*)(r31 + 0x2348) = f26
	#800dfd94: stfs	f27, 0x234C (r31)
	*(float*)(r31 + 0x234C) = f27
	#800dfd98: stfs	f28, 0x2350 (r31)
	*(float*)(r31 + 0x2350) = f28
	#800dfd9c: stfs	f29, 0x2354 (r31)
	*(float*)(r31 + 0x2354) = f29
	#800dfda0: stfs	f30, 0x2358 (r31)
	*(float*)(r31 + 0x2358) = f30
	#800dfda4: stfs	f31, 0x235C (r31)
	*(float*)(r31 + 0x235C) = f31
	#800dfda8: lwz	r0, 0x009C (sp)
	r0 = *(r1 + 0x009C)
	#800dfdac: lfd	f31, 0x0090 (sp)
	f31 = *(double*)(r1 + 0x0090)
	#800dfdb0: lfd	f30, 0x0088 (sp)
	f30 = *(double*)(r1 + 0x0088)
	#800dfdb4: lfd	f29, 0x0080 (sp)
	f29 = *(double*)(r1 + 0x0080)
	#800dfdb8: lfd	f28, 0x0078 (sp)
	f28 = *(double*)(r1 + 0x0078)
	#800dfdbc: lfd	f27, 0x0070 (sp)
	f27 = *(double*)(r1 + 0x0070)
	#800dfdc0: lfd	f26, 0x0068 (sp)
	f26 = *(double*)(r1 + 0x0068)
	#800dfdc4: lwz	r31, 0x0064 (sp)
	r31 = *(r1 + 0x0064)
	#800dfdc8: lwz	r30, 0x0060 (sp)
	r30 = *(r1 + 0x0060)
	#800dfdcc: lwz	r29, 0x005C (sp)
	r29 = *(r1 + 0x005C)
	#800dfdd0: addi	sp, sp, 152
	sp = r1 + 152 
	#800dfdd4: mtlr	r0
	lr = r0
	#800dfdd8: blr	
	goto LR

fn AS_WalkAnimChange(f1=,f2=SlowWalkAnimLength,f3=WalkAnimLength,f4=FastWalkAnimLength,f5=SlowWalkSpeed,f6=WalkSpeed,f7=FastWalkSpeed,f8=Multiplier?)->void?
@Callstack:
	AS_WalkAnimChange
	AS_WalkAnimChangePrefunction
	AS_WalkAnimChangePrefunction
	Interrupt_Walk
	Interrupt_AS_Wait
	PlayerThink_Interrupt
	GObjProc
	updateFunction
	Scene_ProcessMinor
	Scene_ProcessMajor
	Scene_Main
	main
@Assembly
	800dfca4: mflr	r0
	800dfca8: stw	r0, 0x0004 (sp)
	800dfcac: stwu	sp, -0x0098 (sp)
	800dfcb0: stfd	f31, 0x0090 (sp)
	800dfcb4: fmr	f31, f7
	800dfcb8: stfd	f30, 0x0088 (sp)
	800dfcbc: fmr	f30, f6
	800dfcc0: stfd	f29, 0x0080 (sp)
	800dfcc4: fmr	f29, f5
	800dfcc8: stfd	f28, 0x0078 (sp)
	800dfccc: fmr	f28, f4
	800dfcd0: stfd	f27, 0x0070 (sp)
	800dfcd4: fmr	f27, f3
	800dfcd8: stfd	f26, 0x0068 (sp)
	800dfcdc: fmr	f26, f2
	800dfce0: stw	r31, 0x0064 (sp)
	800dfce4: stw	r30, 0x0060 (sp)
	800dfce8: mr	r30, r4
	800dfcec: stw	r29, 0x005C (sp)
	800dfcf0: mr	r29, r3
	800dfcf4: lwz	r31, 0x002C (r3)
	800dfcf8: stfs	f8, 0x2360 (r31)
	800dfcfc: lwz	r3, 0x002C (r3)
	800dfd00: lfs	f0, -0x6890 (rtoc)
	800dfd04: lfs	f2, 0x00EC (r3)
	800dfd08: fcmpo	cr0,f2,f0
	800dfd0c: bge-	 ->0x800DFD14
	800dfd10: fneg	f2,f2
	800dfd14: lwz	r4, -0x514C (r13)
	800dfd18: lfs	f4, 0x0118 (r3)
	800dfd1c: lfs	f0, 0x002C (r4)
	800dfd20: lfs	f3, 0x2360 (r3)
	800dfd24: fmuls	f0,f0,f4
	800dfd28: fmuls	f0,f3,f0
	800dfd2c: fcmpo	cr0,f2,f0
	800dfd30: cror	2, 1, 2
	800dfd34: bne-	 ->0x800DFD40
	800dfd38: li	r0, 2
	800dfd3c: b	->0x800DFD64
	800dfd40: lfs	f0, 0x0028 (r4)
	800dfd44: fmuls	f0,f0,f4
	800dfd48: fmuls	f0,f3,f0
	800dfd4c: fcmpo	cr0,f2,f0
	800dfd50: cror	2, 1, 2
	800dfd54: bne-	 ->0x800DFD60
	800dfd58: li	r0, 1
	800dfd5c: b	->0x800DFD64
	800dfd60: li	r0, 0
	800dfd64: lfs	f2, -0x688C (rtoc)
	800dfd68: add	r4, r30, r0
	800dfd6c: lfs	f3, -0x6890 (rtoc)
	800dfd70: mr	r3, r29
	800dfd74: li	r6, 0
	800dfd78: bl	->0x800693AC
	800dfd7c: mr	r3, r29
	800dfd80: bl	->0x8006EBA4 AS_AnimationFrameUpdate&More
	800dfd84: lfs	f0, 0x00EC (r31)
	800dfd88: stfs	f0, 0x2340 (r31)
	800dfd8c: stw	r30, 0x2344 (r31)
	800dfd90: stfs	f26, 0x2348 (r31)
	800dfd94: stfs	f27, 0x234C (r31)
	800dfd98: stfs	f28, 0x2350 (r31)
	800dfd9c: stfs	f29, 0x2354 (r31)
	800dfda0: stfs	f30, 0x2358 (r31)
	800dfda4: stfs	f31, 0x235C (r31)
	800dfda8: lwz	r0, 0x009C (sp)
	800dfdac: lfd	f31, 0x0090 (sp)
	800dfdb0: lfd	f30, 0x0088 (sp)
	800dfdb4: lfd	f29, 0x0080 (sp)
	800dfdb8: lfd	f28, 0x0078 (sp)
	800dfdbc: lfd	f27, 0x0070 (sp)
	800dfdc0: lfd	f26, 0x0068 (sp)
	800dfdc4: lwz	r31, 0x0064 (sp)
	800dfdc8: lwz	r30, 0x0060 (sp)
	800dfdcc: lwz	r29, 0x005C (sp)
	800dfdd0: addi	sp, sp, 152
	800dfdd4: mtlr	r0
	800dfdd8: blr

################################################################################################
# Player Physics functions
################################################################################################

fn PlayerThink_Physics@0x8006b82c(PlayerEntityStruct* pPlayerEntityStruct@r3)->void
@PseudoAssembly:
	# save r26..r31, f30, f31 on the stackframe
	# stackframe for local variables has size 0x68. Stack variable storage is notated as varName@sp0x32 to refer to the variable at sp+0x32=r1+0x32.
	
	# duplicate registers
	pPlayerEntityStruct@r28 = pPlayerEntityStruct@r3
	
	CharData* pCharData@r3 = pPlayerEntityStruct@r3.pCharData@0x2C
	pCharData@r31 = pCharData@r3
	
	if pCharData@r3.bitfield@0x221F & 0b10000: # 'sleep' bit according to m-Ex figher.h, should this be called not_sleeping instead?
		return
	
	# all wind hazards like wispy are accumulated into this vector at the end of the following then-block, and set to 0 in the else-block.
	# => The bit tested in the if-condition might test if the player is active or not (not active when dead/respawning/on the angel platform)
	Vec3 windOffset@sp0x4C
	
	#8006b85c
	if pCharData@r31.VariousFlags(byte)@0x2219 & 0b100 == 0: # 'freeze' bit according to m-Ex fighter.h
		#8006b868
		if pCharData@r31.ledgeGrabCooldown(int)@0x2064 != 0:
			pCharData@r31.ledgeGrabCooldown(int)@0x2064 -= 1
		
		# I was not able to trigger the following counter. Even with a memory breakpoint,
		# this value was only read by HSD_DObjAnimAll at 8035e07c. Here's what I tested:
		# smash attack charge timer
		# grab timer
		# shield break tumble timer
		# hitlag/hitstun timer
		# ledge grab timer
		# L-cancel window
		# tech window
		# Barrel timer
		# Peach float timer
		# Item regrab cooldown after throwing with A or c-stick
		# TODO: TEST VARIOUS ITEM TIMERS (tested until home run bat so far)
		# The value is also written to every time the UnclePunch conversion training resets, but
		# that's probably just UnclePunch code.
		if pCharData@r31.int@0x2108 != 0: # TODO: undocumented character data
			pCharData@r31.int@0x2108 -= 1
		
		FtChkDevice_DecrementImmunity@0x800C0A98(r3 = pPlayerEntityStruct@r28)
		
		# I think this calls the main physics function for states like walk/jump/attack
		#8006b85c
		FUNC_PTR AS_Physics_Func@r12 = pCharData@r31.CurrerntActionStatePhysicsPtr@0x21A4
		if AS_Physics_Func@r12 != 0:
			AS_Physics_Func@r12(r3 = pPlayerEntityStruct@r28)
		
		#8006B8B0 Update knockback, and (when transitioning to the ground?) also the velocity:
		# when airborne:
		# - reduce knockback magnitude by knockbackDecay
		# - unless some (debugging?) flag is set, then reduces knockback velocity x and y individually by the x and y components of pCharData.vec2@0x2D4.
		# - always set ground_kb_vel = 0
		# when grounded:
		# - when ground_kb_vel==0, set it to knockbackVel.x (this might have some unintended implications)
		# - reduce ground_kb_vel magnitude slightly
		# - Then set knockbackVel = groundVel.x * surfaceTangent.
		float* p_kb_vel@r30 = &pCharData@r31.knockbackVel@0x8C
		float kb_vel_x@f2 = pCharData@r31.knockbackVel@0x8C.x
		if p_kb_vel@r30.xy != vec2(0): # 0.0f@f1 = 0.0f@toc-0x778C; (0.0f@f1 != kb_vel_x@f2) || (0.0f@f1 != p_kb_vel@r30.y@0x4):
			#8006B8D0
			if pCharData@r31.airborne(int)@0xE0 == 1: # 0=grounded, 1=airborne.
				float kb_vel_x@f31 = p_kb_vel@r30.x@0x0
				float kb_vel_y@f30 = p_kb_vel@r30.y@0x4
				if pCharData@r31.bitFlags@0x2228 & 0b10_0000: # I was not able to trigger this case in normal gameplay yet. spreadsheet comment: facing angle? hi-pitch, lo-pitch, noCliffCatch
					p_kb_vel@r30.x = reduceMagnitude@0x8007CD6C(p_kb_vel@r30.x, getVec0x2D4_X_assertPlayerIndex@0x8007CDA4(r3 = pCharData@r31))
					p_kb_vel@r30.y = reduceMagnitude@0x8007CD6C(p_kb_vel@r30.y, getVec0x2D4_Y_assertPlayerIndex@0x8007cdf8(r3 = pCharData@r31))
				else: #@0x8006b924
					# Conceptually the next code block does this:
					# 	float kb_vel_len@f4 = sqrt(kb_vel_x@f31 * kb_vel_x@f31 + kb_vel_y@f30 * kb_vel_y@f30)
					# But the following code is an explicit square root implementation (Probably because
					# the compiler inlined the square root). To compute the square root of S, first a rough
					# approximation x of 1/sqrt(S) is computed using the assembly instruction frsqrte, which has
					# a relative error less than 1/32. Next Newton's method is used to find the root of the equation
					#    f(x) := 1/x^2 - S = 0.
					# Newton's method to solve for f(x)=0 uses the iteration x_{n+1} = x_n - f(x)/f'(x).
					# This leads to the iteration formula:
					# 	x_{n+1} = x_n * (3 - S * x_n^2)/2,  n=0,1,2,...
					# This formula is iterated three times, then x is a very good approximation of
					# 1/sqrt(S). Therefore x*S is a very good approximation of sqrt(S).
					float S = kb_vel_x@f31 * kb_vel_x@f31 + kb_vel_y@f30 * kb_vel_y@f30
					float x
					if S > 0:
						float x = approx_rsqrt(S) # rough approximation of 1/sqrt(S)
						loop 3 times:
							# The constants are stored at TOC.double@-0x7758=3 and TOC.double@-0x7760=0.5
							x *= 0.5 * (3 - S * x*x)
						x *= S # now x is a very good approximation of the square root of S
					else:
						x = 0
					float kb_vel_len@f4 = x
					
					# decrement knockback velocity magnitude
					float kb_vel_decrement = p_stc_ftcommon@(r13-0x514c).kb_frameDecay@0x204 # = 0.051 constant?
					if kb_vel_len@f4 < kb_vel_decrement:
						*p_kb_vel@r30 = vec2(0) # = vec2(0.0f@toc-0x778C, 0.0f@toc-0x778C)
					else:
						# What we want to achieve is this:
						# 	*p_kb_vel *= (kb_vel_len - kb_vel_decrement)/kb_vel_len
						# But this is implemented very inefficiently like this:
						float kb_angle = atan2@0x80022C30(kb_vel_y, kb_vel_x)
						vec2 normalized_kb_vel = vec2(cos@8006b9b8(kb_angle), sin@8006b9d4(kb_angle)) # kb_vel / kb_vel_len would be better still
						*p_kb_vel@r30 -= kb_vel_decrement * normalized_kb_vel
				pCharData@r31.ground_kb_vel@0xF0 = 0 # = 0.0f@toc-0x778C
			else: #8006b9f8
				# This is probably triggered when transitioning from the air to the ground, for example with ASDI down after getting hit.
				if pCharData@r31.ground_kb_vel@0xF0 == 0:
					pCharData@r31.ground_kb_vel@0xF0 = kb_vel_x@f2
				float effectiveFriction = pCharData@r31.friction@0x128 * Stage_GetGroundFrictionMultiplier@0x80084A40(r3 = pCharData@r31) * p_stc_ftcommon@(r13-0x514c).float?@0x200 # ground multiplier usually 1. last factor was 1 when I looked
				reduceGroundKnockbackVel@0x8007CCA0(r3 = pCharData@r31, f1 = effectiveFriction)
				# set knockback velocity to ground_kb_vel * surfaceTangent
				Vec2* pNormal@r29 = &pCharData@r31.surfaceNormal@0x844 # surface normal points out of the surface.
				*(p_kb_vel@r30) = pCharData@r31.ground_kb_vel@0xF0 * Vec2(pNormal@r29.y@0x4, -pNormal@r29.x@0x0)
		
 		#8006BA5C Now handle the attacker's shield knockback in a similar way
		Vec3* pAtkShieldKB@r29 = &pCharData@r31.atkShieldKB@0x98
		float atkShieldKB_X@f2 = pCharData@r31.atkShieldKB@0x98.x
		if pCharData@r31.atkShieldKB@0x98.xy != vec2(0,0):
			if pCharData@r31.airborne(int)@0xE0 == 1: # = vec2(0.0f@toc-0x778C, 0.0f@toc-0x778C)
				#8006ba88
				vec2 atkShieldKB = pCharData@r31.atkShieldKB@0x98.xy
				# The following square root was inlined to a large Newton approximation of this
				# inverse square root just as a few lines above. I'll just write the result here:
				float atkShieldKB_len@f4 = sqrt(atkShieldKB.x * atkShieldKB.x + atkShieldKB.y * atkShieldKB.y)
				float len_decrement = p_stc_ftcommon@(r13-0x514c).shield_kb_frameDecay@0x3E8 # TODO: document this
				if atkShieldKB_len@f4 < len_decrement:
					pAtkShieldKB@r29.x@0x0 = 0
					# BUG IN THE MELEE CODE THAT CAUSES THE INVISIBLE CEILING GLITCH
					# The next line should be 'pAtkShieldKB.y = 0', but instead it is:
					p_kb_vel@r30.y@0x4 = 0
				else:
					# again, the better implementation would be:
					#	*pAtkShieldKB *= (atkShieldKB_len - len_decrement)/atkShieldKB_len
					float atkShieldKBAngle = atan2(atkShieldKB.y, atkShieldKB.x)
					*(pAtkShieldKB@r29) -= len_decrement * Vec2(cos(atkShieldKBAngle), sin(atkShieldKBAngle))
				pCharData@r31.ground_shield_kb_vel@0xF4 = 0 # 0 = TOC.float@-0x778C
			else: #8006bb64
				if pCharData@r31.ground_shield_kb_vel@0xF4 == 0:
					pCharData@r31.ground_shield_kb_vel@0xF4 = atkShieldKB_X@f2
				float effectiveFriction = pCharData@r31.friction@0x128 * Stage_GetGroundFrictionMultiplier@0x80084A40(r3 = pCharData@r31) * p_stc_ftcommon@(r13-0x514c).float?@0x03EC # This last constant variable differs from the one for the knockback friction above
				reduceGroundShieldKnockbackVel@0x8007CE4C(r3 = pCharData@r31, f1 = effectiveFriction)
				Vec2* pNormal@r27 = &pCharData@r31.surfaceNormal@0x844
				*(pAtkShieldKB@r29) = pCharData@r31.ground_shield_kb_vel@0xF4 * Vec2(pNormal@r27.y@0x4, -pNormal@r27.x@0x0)
		
		#8006BBC8 update horizontalSelfVel
		pCharData@r31.groundVel@0xEC += pCharData@r31.groundAccel1@0xE4 + pCharData@r31.groundAccel2@0xE8
		pCharData@r31.groundAccel1@0xE4 = 0
		pCharData@r31.groundAccel2@0xE8 = 0
		#PSVECAdd@0x80342D54(r3=&pCharData@r31.selfVel@0x80, r4=&pCharData@r31.accel@0x74, r5=&pCharData@r31.selfVel@0x80)
		pCharData@r31.selfVel@0x80.xyz += pCharData@r31.accel@0x74.xyz
		pCharData@r31.accel@0x74 = Vec3(0)
		
		# copy selfVel into a stack storage variable
		Vec3 selfVel@sp0x40 = pCharData@r31.selfVel@0x80
		
		# TODO: these double_lower_32bit variables are probably integer counters that get decremented each frame.
		# The double value construction then is only used as an interpoltion tool between selfVel and some UnkVel2.
		uint double_lower_32bits_1@r0 = pCharData@r31.double_lower_32bits_1@0x1948
		if double_lower_32bits_1@r0 != 0:
			# bit construction of two doubles on the stack. The flags count as mantissa bits. Withouth these flags,
			# the bytes 0x4330_0000_0000_0000, interpreted as a double, give the decimal value 4_503_599_627_370_496, and a bit higher with mantissa bits.
			uint[2] doubleA@sp0x58 = [0x43300000, double_lower_32bits_1@r0 ^ (1 << 31)] # highest bit is flipped
			uint[2] doubleB@sp0x60 = [0x43300000, pCharData@r31.double_lower_32bits_2@0x194C ^ (1 << 31)]  # highest bit is flipped
			double A@f0 = raw_cast(double)doubleA@sp0x58
			double B@f1 = raw_cast(double)doubleB@sp0x60
			
			float C@f2 = TOC@r2.float@-0x7790 - (B - TOC@r2.double@-0x7780) / (A - TOC@r2.double@-0x7780)
			selfVel@sp0x40.xy = C@f2 * (pCharData@r31.selfVel@0x80.xy - pCharData@r31.UnkVel2@0xA4.xy) + pCharData@r31.UnkVel2@0xA4.xy
			if --pCharData@r31.double_lower_32bits_2@0x194C == 0:
				pCharData@r31.double_lower_32bits_1@0x1948 = 0
		# add some horizontal+depth offset to the position? Why is there no vertical component?
		pCharData@r31.position@0xB0.x += pCharData@r31.float@0xF8
		pCharData@r31.position@0xB0.z += pCharData@r31.float@0xFC
		if (double_lower_32bits_1@r0 & 0b10) && !(pCharData@r31.byte@0x2222 & 0b01):
			#PSVECAdd@0x80342D54(r3 = &pCharData@r31.unkVec@0xD4, r4 = &selfVel@sp0x40, r5 = r3)
			pCharData@r31.unkVec@0xD4.xyz += p_kb_vel@r30.xyz
			
			bool bit@r0 = pCharData@r31.partUnkFlags(ubyte)@0x2210.bits[5] # bits[0] being the least significant bit
			pCharData@r31.partUnkFlags(ubyte)@0x2210.bits[5] = 0
			
			if bit@r0 || (CALL(0x80070FD0)(r3 = pCharData@r31); r3 != 0) || (pCharData@r31.ubyte@0x594 & 1):
				#PSVECAdd@0x80342D54(r3 = &pCharData@r31.position@0xB0, r4 = pCharData@r31.unkVec@0xD4, r5 = r3)
				pCharData@r31.position@0xB0.xyz += pCharData@r31.unkVec?@0xD4.xyz
				pCharData@r31.unkVec?@0xD4 = vec3(0) # = 0.0f@toc-0x778C) TODO: we set this velocity to 0 after applying it -> Is this SDI or ASDI?
			#PSVECAdd@0x80342D54(r3 = &pCharData@r31.position@0xB0, r4 = pAtkShieldKB@r29, r5 = r3)
			pCharData@r31.position@0xB0.xyz += pAtkShieldKB@r29.xyz
		else:
			#PSVECAdd@0x80342D54(r3 = &pCharData@r31.position@0xB0, r4 = &pCharData@r31.position@0xB0, r5 = r3)
			#PSVECAdd@0x80342D54(r3 = &pCharData@r31.position@0xB0, r4 = pAtkShieldKB@r29, r5 = r3)
			pCharData@r31.position@0xB0.xyz += selfVel@sp0x40.xyz + pAtkShieldKB@r29.xyz
			pCharData@r31.position@0xB0.xy  += p_kb_vel@r30.xy
		# accumulate wind hazards into the windOffset vector
		Stage_CheckForWindHazards@0x8007B924(r3 = pPlayerEntityStruct@r28, /*result vec3*/r4 = &windOffset@sp0x4C)
	else: # 0x8006bde8
		Vec3 windOffset@sp0x4C = Vec(0) # the 0.0f constant below is from f0 = TOC@r2.float@-0x778C
	DataOffset_ComboCount_TopNAttackerModify@0x80076528(r3 = pPlayerEntityStruct@r28)
	
	#8006be00 void (*EveryHitlag_x21D0)(GOBJ *fighter)
	FuncPtr hitlagFn@r12 = pCharData@r31.EveryHitlag_x21D0@0x21D0
	if hitlagFn@r12 != 0:
		hitlagFn@r12(r3 = pPlayerEntityStruct@r28)
	
	#8006be18
	if pCharData@r31.airborne(int)@0xE0 == 0:
		Vec3 difference@sp0x24
		# I think this function always returns r3=1, but it contains two __assert functions. But I guess these just stop or reset the game.
		# result is written to where r5 points to, which is 'difference' in this case
		bool res@r3 = Collision_GetPositionDifference@0x800567C0(/*GroundID*/r3 = pCharData@r31.groundID?@0x83C/*groundID field not documented*/, /*Vec3*/r4 = &pCharData@r31.position@0xB0, r5 = &difference@sp0x24)
		if res@r3:
			#PSVECAdd@0x80342D54(r3 = &pCharData@r31.position@0xB0, &difference@sp0x24, r5 = r3)
			pCharData@r31.position@0xB0 += difference@sp0x24
	
	#8006be4c
	pCharData@r31.position@0xB0.xyz += localVec@sp0x4C.xyz
	
	#8006be80 TODO: do the bitflag tests here tell us if the player is dead?
	Player_CheckForDeath@0x800D3158(r3 = pPlayerEntityStruct@r28)
	if pCharData@r31.byte@0x2225.bits[7]: # bit[0] = least significant
		# if position.y crossed (0.25*stage.blastBottom+0.75*stage.cameraBottom) + stage.crowdReactStart from below...
		if pCharData@r31.prevPositionY@0xC0 <= StageInfo_CrowdGaspHeight?@0x80224BC4() &&
		   pCharData@r31.position@0xB0.y    >  StageInfo_CrowdGaspHeight?@0x80224BC4():
			pCharData@r31.byte@0x2225.bits[7] = 0 # bit[0] = least significant bit
	else:
		if (pCharData@r31.byte@0x222A.bits[6] == 0) && (pCharData@r31.byte@0x2228.bits[2] == 0):
			# if position.y crossed 0.5*(stage.blastBottom+stage.cameraBottom) + stage.crowdReactStart from above...
			if pCharData@r31.prevPositionY@0xC0 >= StageInfo_OffscreenBottomLoad@0x80224B98() &&
			   pCharData@r31.position@0xB0.y < StageInfo_OffscreenBottomLoad@0x80224B98():
				# plays this sound you always hear when you get close to the bottom blast zone
				SFX_PlayCharacterSFX@0x80088148(r3 = r31, r4 = 96, r5 = 127, r6 = 64)
				pCharData@r31.byte@0x2225.bits[7] = 1 # bits[0] = least significant bit
	#8006bf28
	if pCharData@r31.knockbackMagnitude(float)@0x18A4 != 0 # 0.0f@toc-0x778C
		if pCharData@r31.byte@0x221C & 0b10:
			# not sure when we reach this point, but often around the end of knockback, sometimes completely unrelated
			if !PositionXBetweenLedgesMinDelta@0x80322258(f1 = pCharData@r31.position@0xB0.x):
				pCharData@r31.knockbackMagnitude(float)@0x18A4 = 0 # = 0.0f@toc-0x778C
	Hurtbox_SetAllNotUpdated@0x8007AF28(r3 = pPlayerEntityStruct@r28)
	
	#8006bf64
	if debugLevel(int)?@(r13-0x6C98) <= 3: # This value is zero and I think it always will be. Probably some debug level indicator, because only a NaN test follows next.
		return
	
	#8006bf70: The remaining code does this and then returns, but the isNaN tests are inlined by the compiler.
	if isNaN(pCharData@r31.position.x) || isNaN(pCharData@r31.position.y) || isNaN(pCharData@r31.position.z):
		# I think setting f1 and f2 here has no effect. But maybe the registers are dumped by the OSReport or __assert.
		f1 = pCharData@r31.position@0xB0.x
		f2 = pCharData@r31.position@0xB0.y
		OSReport@0x803456A8(r3 = 0x803C0000 + 1452, CR.bits[6] = 1) # bit[0] = leftmost bit
		__assert@0x80388220(r3 = 0x803C0000 + 1404, r4 = 2517, r5 = r13 - 31888)
	
	# Close to ASM version of the above block:
	# Determine the FloatType of pCharData@r31.position@0xB0.x, write result to r0.
	# This was probably inlined by the compiler.
	enum FloatType { NaN=1, Infinite=2, Zero=3, Normal=4, Subnormal=5 }
	#8006bf70
	uint exponentMask@r0 = 0b01111111100000000000000000000000 # = 0x7F800000
	uint rawPosX@r4 = pCharData@r31.position@0xB0.x
	uint exponentBits@r3 = rawPosX@r4 & 0b01111111100000000000000000000000
	#8006bf84
	if exponentBits@r3 != exponentMask@r0:
		# not all exponent bits set -> a number
		#8006bf8c
		if 0 == exponentBits@r3 < exponentMask@r0: # we already know that '<' is true from the '!=', why test this?
			# no exponent bits set -> subnormal number or zero., including zero when also no fractional bits are set.
			#8006bfb4
			r0 = (rawPosX@r4 & 0b00000000011111111111111111111111) ? FloatType.Subnormal : FloatType.Zero
		else:
			#8006bfcc
			r0 = FloatType.Normal # some but not all exponent bits are set -> normal number
	else:
		# all exponent bits set
		r0 = (rawPosX@r4 & 0b00000000011111111111111111111111) ? FloatType.NaN : FloatType.Infinite
	#8006bfd0
	FloatType posXFloatType@r0 = r0
	
	if posXFloatType@r0 != FloatType.NaN:
		# determine float type of pCharData@r31.position@0xB0.y, result in r0
		f0 = pCharData@r31.position@0xB0.y
		r0 = 0x7F800000
		*(float*)(r1 + 0x0014) = f0
		r4 = *(int32)(r1 + 0x0014)
		r3 = r4 & 0b01111111100000000000000000000000
		if r3 != r0:
			if r3 >= r0 || r0 != 0:
				r0 = 4
			else:
				r0 = (r4 & 0b00000000011111111111111111111111) ? 5 : 3
		else:
			r0 = (r4 & 0b00000000011111111111111111111111) ? 1 : 2
		FloatType posYFloatType@r0 = r0
		if posYFloatType@r0 != FloatType.NaN:
			# determine float type of pCharData@r31.position@0xB0.z, result in r0
			f0 = pCharData@r31.position@0xB0.z
			r0 = 0x7F800000
			*(float*)(r1 + 0x0010) = f0
			r4 = *(int32)(r1 + 0x0010)
			r3 = r4 & 0b01111111100000000000000000000000
			if r3 != r0:
				if r3 <= r0 != 0:
					r0 = (r4 & 0b00000000011111111111111111111111) ? 5 : 3
				else:
					r0 = 4
			else:
				r0 = (r4 & 0b00000000011111111111111111111111) ? 1 : 2
			FloatType posZFloatType@r0 = r0
			
			if posZFloatType@r0 != FloatType.NaN:
				return
	# Setting f1,f2 has no effect, but it's actually in the ASM code.
	# These also can not be return values, because an assertion error is being generated next.
	f1 = pCharData@r31.position@0xB0.x
	f2 = pCharData@r31.position@0xB0.y
	OSReport@0x803456A8(r3 = 0x803C0000 + 1452, CR.bits[6] = 1) # bit[0] = leftmost bit
	__assert@0x80388220(r3 = 0x803C0000 + 1404, r4 = 2517, r5 = r13 - 31888)
	# unwind stackframe and return
@Assembly:
	8006b82c: mflr	r0
	8006b830: stw	r0, 0x0004 (sp)
	8006b834: stwu	sp, -0x0090 (sp)
	8006b838: stfd	f31, 0x0088 (sp)
	8006b83c: stfd	f30, 0x0080 (sp)
	8006b840: stmw	r26, 0x0068 (sp)
	8006b844: mr	r28, r3
	8006b848: lwz	r3, 0x002C (r3)
	8006b84c: lbz	r0, 0x221F (r3)
	8006b850: addi	r31, r3, 0
	8006b854: rlwinm.	r0, r0, 28, 31, 31 (00000010)
	8006b858: bne-	 ->0x8006C0D4
	8006b85c: lbz	r0, 0x2219 (r31)
	8006b860: rlwinm.	r0, r0, 30, 31, 31 (00000004)
	8006b864: bne-	 ->0x8006BDE8
	8006b868: lwz	r3, 0x2064 (r31)
	8006b86c: cmpwi	r3, 0
	8006b870: beq-	 ->0x8006B87C
	8006b874: subi	r0, r3, 1
	8006b878: stw	r0, 0x2064 (r31)
	8006b87c: lwz	r3, 0x2108 (r31)
	8006b880: cmpwi	r3, 0
	8006b884: beq-	 ->0x8006B890
	8006b888: subi	r0, r3, 1
	8006b88c: stw	r0, 0x2108 (r31)
	8006b890: mr	r3, r28
	8006b894: bl	->0x800C0A98
	8006b898: lwz	r12, 0x21A4 (r31)
	8006b89c: cmplwi	r12, 0
	8006b8a0: beq-	 ->0x8006B8B0
	8006b8a4: mtlr	r12
	8006b8a8: addi	r3, r28, 0
	8006b8ac: blrl	
	8006b8b0: lfs	f1, -0x778C (rtoc)
	8006b8b4: addi	r30, r31, 140
	8006b8b8: lfs	f2, 0x008C (r31)
	8006b8bc: fcmpu	cr0,f1,f2
	8006b8c0: bne-	 ->0x8006B8D0
	8006b8c4: lfs	f0, 0x0004 (r30)
	8006b8c8: fcmpu	cr0,f1,f0
	8006b8cc: beq-	 ->0x8006BA5C
	8006b8d0: lwz	r0, 0x00E0 (r31)
	8006b8d4: cmpwi	r0, 1
	8006b8d8: bne-	 ->0x8006B9F8
	8006b8dc: lbz	r0, 0x2228 (r31)
	8006b8e0: lfs	f31, 0 (r30)
	8006b8e4: rlwinm.	r0, r0, 27, 31, 31 (00000020)
	8006b8e8: lfs	f30, 0x0004 (r30)
	8006b8ec: beq-	 ->0x8006B924
	8006b8f0: mr	r3, r31
	8006b8f4: bl	->0x8007CDA4
	8006b8f8: fmr	f2, f1
	8006b8fc: lfs	f1, 0 (r30)
	8006b900: bl	->0x8007CD6C
	8006b904: stfs	f1, 0 (r30)
	8006b908: mr	r3, r31
	8006b90c: bl	->0x8007CDF8
	8006b910: fmr	f2, f1
	8006b914: lfs	f1, 0x0004 (r30)
	8006b918: bl	->0x8007CD6C
	8006b91c: stfs	f1, 0x0004 (r30)
	8006b920: b	->0x8006B9EC
	8006b924: fmr	f1, f30
	8006b928: fmr	f2, f31
	8006b92c: bl	->0x80022C30
	8006b930: fmuls	f2,f30,f30
	8006b934: lfs	f0, -0x778C (rtoc)
	8006b938: fmadds	f4,f31,f31,f2
	8006b93c: fmr	f31, f1
	8006b940: fcmpo	cr0,f4,f0
	8006b944: ble-	 ->0x8006B994
	8006b948: frsqrte	f1,f4
	8006b94c: lfd	f3, -0x7760 (rtoc)
	8006b950: lfd	f2, -0x7758 (rtoc)
	8006b954: fmul	f0,f1,f1
	8006b958: fmul	f1,f3,f1
	8006b95c: fnmsub	f0,f4,f0,f2
	8006b960: fmul	f1,f1,f0
	8006b964: fmul	f0,f1,f1
	8006b968: fmul	f1,f3,f1
	8006b96c: fnmsub	f0,f4,f0,f2
	8006b970: fmul	f1,f1,f0
	8006b974: fmul	f0,f1,f1
	8006b978: fmul	f1,f3,f1
	8006b97c: fnmsub	f0,f4,f0,f2
	8006b980: fmul	f0,f1,f0
	8006b984: fmul	f0,f4,f0
	8006b988: frsp	f0,f0
	8006b98c: stfs	f0, 0x0020 (sp)
	8006b990: lfs	f4, 0x0020 (sp)
	8006b994: lwz	r3, -0x514C (r13)
	8006b998: lfs	f0, 0x0204 (r3)
	8006b99c: fcmpo	cr0,f4,f0
	8006b9a0: bge-	 ->0x8006B9B4
	8006b9a4: lfs	f0, -0x778C (rtoc)
	8006b9a8: stfs	f0, 0x0004 (r30)
	8006b9ac: stfs	f0, 0 (r30)
	8006b9b0: b	->0x8006B9EC
	8006b9b4: fmr	f1, f31
	8006b9b8: bl	->0x80326240
	8006b9bc: lwz	r3, -0x514C (r13)
	8006b9c0: lfs	f0, 0 (r30)
	8006b9c4: lfs	f2, 0x0204 (r3)
	8006b9c8: fnmsubs	f0,f2,f1,f0
	8006b9cc: fmr	f1, f31
	8006b9d0: stfs	f0, 0 (r30)
	8006b9d4: bl	->0x803263D4
	8006b9d8: lwz	r3, -0x514C (r13)
	8006b9dc: lfs	f0, 0x0004 (r30)
	8006b9e0: lfs	f2, 0x0204 (r3)
	8006b9e4: fnmsubs	f0,f2,f1,f0
	8006b9e8: stfs	f0, 0x0004 (r30)
	8006b9ec: lfs	f0, -0x778C (rtoc)
	8006b9f0: stfs	f0, 0x00F0 (r31)
	8006b9f4: b	->0x8006BA5C
	8006b9f8: lfs	f1, -0x778C (rtoc)
	8006b9fc: addi	r29, r31, 2116
	8006ba00: lfs	f0, 0x00F0 (r31)
	8006ba04: fcmpu	cr0,f1,f0
	8006ba08: bne-	 ->0x8006BA10
	8006ba0c: stfs	f2, 0x00F0 (r31)
	8006ba10: addi	r27, r31, 272
	8006ba14: addi	r3, r31, 0
	8006ba18: bl	->0x80084A40
	8006ba1c: lfs	f0, 0x0018 (r27)
	8006ba20: mr	r3, r31
	8006ba24: lwz	r4, -0x514C (r13)
	8006ba28: fmuls	f1,f0,f1
	8006ba2c: lfs	f0, 0x0200 (r4)
	8006ba30: fmuls	f1,f0,f1
	8006ba34: bl	->0x8007CCA0
	8006ba38: lfs	f1, 0x0004 (r29)
	8006ba3c: lfs	f0, 0x00F0 (r31)
	8006ba40: fmuls	f0,f1,f0
	8006ba44: stfs	f0, 0 (r30)
	8006ba48: lfs	f1, 0 (r29)
	8006ba4c: lfs	f0, 0x00F0 (r31)
	8006ba50: fneg	f1,f1
	8006ba54: fmuls	f0,f1,f0
	8006ba58: stfs	f0, 0x0004 (r30)
	8006ba5c: lfs	f1, -0x778C (rtoc)
	8006ba60: addi	r29, r31, 152
	8006ba64: lfs	f2, 0x0098 (r31)
	8006ba68: fcmpu	cr0,f1,f2
	8006ba6c: bne-	 ->0x8006BA7C
	8006ba70: lfs	f0, 0x0004 (r29)
	8006ba74: fcmpu	cr0,f1,f0
	8006ba78: beq-	 ->0x8006BBC8
	8006ba7c: lwz	r0, 0x00E0 (r31)
	8006ba80: cmpwi	r0, 1
	8006ba84: bne-	 ->0x8006BB64
	8006ba88: lfs	f30, 0 (r29)
	8006ba8c: lfs	f31, 0x0004 (r29)
	8006ba90: fmr	f2, f30
	8006ba94: fmr	f1, f31
	8006ba98: bl	->0x80022C30
	8006ba9c: fmuls	f2,f31,f31
	8006baa0: lfs	f0, -0x778C (rtoc)
	8006baa4: fmr	f31, f1
	8006baa8: fmadds	f4,f30,f30,f2
	8006baac: fcmpo	cr0,f4,f0
	8006bab0: ble-	 ->0x8006BB00
	8006bab4: frsqrte	f1,f4
	8006bab8: lfd	f3, -0x7760 (rtoc)
	8006babc: lfd	f2, -0x7758 (rtoc)
	8006bac0: fmul	f0,f1,f1
	8006bac4: fmul	f1,f3,f1
	8006bac8: fnmsub	f0,f4,f0,f2
	8006bacc: fmul	f1,f1,f0
	8006bad0: fmul	f0,f1,f1
	8006bad4: fmul	f1,f3,f1
	8006bad8: fnmsub	f0,f4,f0,f2
	8006badc: fmul	f1,f1,f0
	8006bae0: fmul	f0,f1,f1
	8006bae4: fmul	f1,f3,f1
	8006bae8: fnmsub	f0,f4,f0,f2
	8006baec: fmul	f0,f1,f0
	8006baf0: fmul	f0,f4,f0
	8006baf4: frsp	f0,f0
	8006baf8: stfs	f0, 0x001C (sp)
	8006bafc: lfs	f4, 0x001C (sp)
	8006bb00: lwz	r3, -0x514C (r13)
	8006bb04: lfs	f0, 0x03E8 (r3)
	8006bb08: fcmpo	cr0,f4,f0
	8006bb0c: bge-	 ->0x8006BB20
	8006bb10: lfs	f0, -0x778C (rtoc)
	8006bb14: stfs	f0, 0x0004 (r30)
	8006bb18: stfs	f0, 0 (r29)
	8006bb1c: b	->0x8006BB58
	8006bb20: fmr	f1, f31
	8006bb24: bl	->0x80326240
	8006bb28: lwz	r3, -0x514C (r13)
	8006bb2c: lfs	f0, 0 (r29)
	8006bb30: lfs	f2, 0x03E8 (r3)
	8006bb34: fnmsubs	f0,f2,f1,f0
	8006bb38: fmr	f1, f31
	8006bb3c: stfs	f0, 0 (r29)
	8006bb40: bl	->0x803263D4
	8006bb44: lwz	r3, -0x514C (r13)
	8006bb48: lfs	f0, 0x0004 (r29)
	8006bb4c: lfs	f2, 0x03E8 (r3)
	8006bb50: fnmsubs	f0,f2,f1,f0
	8006bb54: stfs	f0, 0x0004 (r29)
	8006bb58: lfs	f0, -0x778C (rtoc)
	8006bb5c: stfs	f0, 0x00F4 (r31)
	8006bb60: b	->0x8006BBC8
	8006bb64: lfs	f1, -0x778C (rtoc)
	8006bb68: addi	r27, r31, 2116
	8006bb6c: lfs	f0, 0x00F4 (r31)
	8006bb70: fcmpu	cr0,f1,f0
	8006bb74: bne-	 ->0x8006BB7C
	8006bb78: stfs	f2, 0x00F4 (r31)
	8006bb7c: addi	r26, r31, 272
	8006bb80: addi	r3, r31, 0
	8006bb84: bl	->0x80084A40
	8006bb88: lfs	f0, 0x0018 (r26)
	8006bb8c: mr	r3, r31
	8006bb90: lwz	r4, -0x514C (r13)
	8006bb94: fmuls	f1,f0,f1
	8006bb98: lfs	f0, 0x03EC (r4)
	8006bb9c: fmuls	f1,f0,f1
	8006bba0: bl	->0x8007CE4C
	8006bba4: lfs	f1, 0x0004 (r27)
	8006bba8: lfs	f0, 0x00F4 (r31)
	8006bbac: fmuls	f0,f1,f0
	8006bbb0: stfs	f0, 0 (r29)
	8006bbb4: lfs	f1, 0 (r27)
	8006bbb8: lfs	f0, 0x00F4 (r31)
	8006bbbc: fneg	f1,f1
	8006bbc0: fmuls	f0,f1,f0
	8006bbc4: stfs	f0, 0x0004 (r29)
	8006bbc8: lfs	f1, 0x00E4 (r31)
	8006bbcc: addi	r3, r31, 128
	8006bbd0: lfs	f0, 0x00E8 (r31)
	8006bbd4: mr	r5, r3
	8006bbd8: lfs	f2, 0x00EC (r31)
	8006bbdc: fadds	f0,f1,f0
	8006bbe0: addi	r4, r31, 116
	8006bbe4: fadds	f0,f2,f0
	8006bbe8: stfs	f0, 0x00EC (r31)
	8006bbec: lfs	f0, -0x778C (rtoc)
	8006bbf0: stfs	f0, 0x00E8 (r31)
	8006bbf4: stfs	f0, 0x00E4 (r31)
	8006bbf8: bl	->0x80342D54
	8006bbfc: lfs	f0, -0x778C (rtoc)
	8006bc00: stfs	f0, 0x007C (r31)
	8006bc04: stfs	f0, 0x0078 (r31)
	8006bc08: stfs	f0, 0x0074 (r31)
	8006bc0c: lwz	r3, 0x0080 (r31)
	8006bc10: lwz	r0, 0x0084 (r31)
	8006bc14: stw	r3, 0x0040 (sp)
	8006bc18: stw	r0, 0x0044 (sp)
	8006bc1c: lwz	r0, 0x0088 (r31)
	8006bc20: stw	r0, 0x0048 (sp)
	8006bc24: lwz	r0, 0x1948 (r31)
	8006bc28: cmpwi	r0, 0
	8006bc2c: beq-	 ->0x8006BCB8
	8006bc30: lwz	r3, 0x194C (r31)
	8006bc34: xoris	r0, r0, 0x8000
	8006bc38: stw	r0, 0x005C (sp)
	8006bc3c: lis	r0, 0x4330
	8006bc40: xoris	r3, r3, 0x8000
	8006bc44: stw	r3, 0x0064 (sp)
	8006bc48: lfd	f3, -0x7780 (rtoc)
	8006bc4c: stw	r0, 0x0060 (sp)
	8006bc50: lfs	f4, -0x7790 (rtoc)
	8006bc54: stw	r0, 0x0058 (sp)
	8006bc58: lfd	f1, 0x0060 (sp)
	8006bc5c: lfd	f0, 0x0058 (sp)
	8006bc60: fsubs	f2,f1,f3
	8006bc64: lfs	f5, 0x00A4 (r31)
	8006bc68: fsubs	f1,f0,f3
	8006bc6c: lfs	f0, 0x0080 (r31)
	8006bc70: fsubs	f0,f0,f5
	8006bc74: fdivs	f1,f2,f1
	8006bc78: fsubs	f2,f4,f1
	8006bc7c: fmadds	f0,f2,f0,f5
	8006bc80: stfs	f0, 0x0040 (sp)
	8006bc84: lfs	f1, 0x00A8 (r31)
	8006bc88: lfs	f0, 0x0084 (r31)
	8006bc8c: fsubs	f0,f0,f1
	8006bc90: fmadds	f0,f2,f0,f1
	8006bc94: stfs	f0, 0x0044 (sp)
	8006bc98: lwz	r3, 0x194C (r31)
	8006bc9c: subi	r0, r3, 1
	8006bca0: stw	r0, 0x194C (r31)
	8006bca4: lwz	r0, 0x194C (r31)
	8006bca8: cmpwi	r0, 0
	8006bcac: bne-	 ->0x8006BCB8
	8006bcb0: li	r0, 0
	8006bcb4: stw	r0, 0x1948 (r31)
	8006bcb8: lfs	f1, 0x00B0 (r31)
	8006bcbc: lfs	f0, 0x00F8 (r31)
	8006bcc0: fadds	f0,f1,f0
	8006bcc4: stfs	f0, 0x00B0 (r31)
	8006bcc8: lfs	f1, 0x00B8 (r31)
	8006bccc: lfs	f0, 0x00FC (r31)
	8006bcd0: fadds	f0,f1,f0
	8006bcd4: stfs	f0, 0x00B8 (r31)
	8006bcd8: lbz	r3, 0x2222 (r31)
	8006bcdc: rlwinm.	r0, r3, 31, 31, 31 (00000002)
	8006bce0: beq-	 ->0x8006BD98
	8006bce4: rlwinm.	r0, r3, 0, 31, 31 (00000001)
	8006bce8: bne-	 ->0x8006BD98
	8006bcec: addi	r3, r31, 212
	8006bcf0: addi	r5, r3, 0
	8006bcf4: addi	r4, sp, 64
	8006bcf8: bl	->0x80342D54
	8006bcfc: lfs	f1, 0x00D4 (r31)
	8006bd00: lfs	f0, 0 (r30)
	8006bd04: fadds	f0,f1,f0
	8006bd08: stfs	f0, 0x00D4 (r31)
	8006bd0c: lfs	f1, 0x00D8 (r31)
	8006bd10: lfs	f0, 0x0004 (r30)
	8006bd14: fadds	f0,f1,f0
	8006bd18: stfs	f0, 0x00D8 (r31)
	8006bd1c: lbz	r3, 0x2210 (r31)
	8006bd20: rlwinm.	r0, r3, 27, 31, 31 (00000020)
	8006bd24: beq-	 ->0x8006BD3C
	8006bd28: li	r0, 0
	8006bd2c: rlwimi	r3, r0, 5, 26, 26 (00000001)
	8006bd30: stb	r3, 0x2210 (r31)
	8006bd34: li	r0, 1
	8006bd38: b	->0x8006BD40
	8006bd3c: li	r0, 0
	8006bd40: cmpwi	r0, 0
	8006bd44: bne-	 ->0x8006BD64
	8006bd48: mr	r3, r31
	8006bd4c: bl	->0x80070FD0
	8006bd50: cmpwi	r3, 0
	8006bd54: bne-	 ->0x8006BD64
	8006bd58: lbz	r0, 0x0594 (r31)
	8006bd5c: rlwinm.	r0, r0, 0, 31, 31 (00000001)
	8006bd60: beq-	 ->0x8006BD84
	8006bd64: addi	r3, r31, 176
	8006bd68: addi	r5, r3, 0
	8006bd6c: addi	r4, r31, 212
	8006bd70: bl	->0x80342D54
	8006bd74: lfs	f0, -0x778C (rtoc)
	8006bd78: stfs	f0, 0x00DC (r31)
	8006bd7c: stfs	f0, 0x00D8 (r31)
	8006bd80: stfs	f0, 0x00D4 (r31)
	8006bd84: addi	r3, r31, 176
	8006bd88: addi	r4, r29, 0
	8006bd8c: addi	r5, r3, 0
	8006bd90: bl	->0x80342D54
	8006bd94: b	->0x8006BDD8
	8006bd98: addi	r3, r31, 176
	8006bd9c: addi	r5, r3, 0
	8006bda0: addi	r4, sp, 64
	8006bda4: bl	->0x80342D54
	8006bda8: lfs	f1, 0x00B0 (r31)
	8006bdac: addi	r3, r31, 176
	8006bdb0: lfs	f0, 0 (r30)
	8006bdb4: addi	r4, r29, 0
	8006bdb8: addi	r5, r3, 0
	8006bdbc: fadds	f0,f1,f0
	8006bdc0: stfs	f0, 0x00B0 (r31)
	8006bdc4: lfs	f1, 0x00B4 (r31)
	8006bdc8: lfs	f0, 0x0004 (r30)
	8006bdcc: fadds	f0,f1,f0
	8006bdd0: stfs	f0, 0x00B4 (r31)
	8006bdd4: bl	->0x80342D54
	8006bdd8: addi	r3, r28, 0
	8006bddc: addi	r4, sp, 76
	8006bde0: bl	->0x8007B924
	8006bde4: b	->0x8006BDF8
	8006bde8: lfs	f0, -0x778C (rtoc)
	8006bdec: stfs	f0, 0x0054 (sp)
	8006bdf0: stfs	f0, 0x0050 (sp)
	8006bdf4: stfs	f0, 0x004C (sp)
	8006bdf8: mr	r3, r28
	8006bdfc: bl	->0x80076528
	8006be00: lwz	r12, 0x21D0 (r31)
	8006be04: cmplwi	r12, 0
	8006be08: beq-	 ->0x8006BE18
	8006be0c: mtlr	r12
	8006be10: addi	r3, r28, 0
	8006be14: blrl	
	8006be18: lwz	r0, 0x00E0 (r31)
	8006be1c: cmpwi	r0, 0
	8006be20: bne-	 ->0x8006BE4C
	8006be24: lwz	r3, 0x083C (r31)
	8006be28: addi	r4, r31, 176
	8006be2c: addi	r5, sp, 36
	8006be30: bl	->0x800567C0
	8006be34: cmpwi	r3, 0
	8006be38: beq-	 ->0x8006BE4C
	8006be3c: addi	r3, r31, 176
	8006be40: addi	r5, r3, 0
	8006be44: addi	r4, sp, 36
	8006be48: bl	->0x80342D54
	8006be4c: lfs	f1, 0x00B0 (r31)
	8006be50: mr	r3, r28
	8006be54: lfs	f0, 0x004C (sp)
	8006be58: fadds	f0,f1,f0
	8006be5c: stfs	f0, 0x00B0 (r31)
	8006be60: lfs	f1, 0x00B4 (r31)
	8006be64: lfs	f0, 0x0050 (sp)
	8006be68: fadds	f0,f1,f0
	8006be6c: stfs	f0, 0x00B4 (r31)
	8006be70: lfs	f1, 0x00B8 (r31)
	8006be74: lfs	f0, 0x0054 (sp)
	8006be78: fadds	f0,f1,f0
	8006be7c: stfs	f0, 0x00B8 (r31)
	8006be80: bl	->0x800D3158
	8006be84: lbz	r0, 0x2225 (r31)
	8006be88: rlwinm.	r0, r0, 25, 31, 31 (00000080)
	8006be8c: beq-	 ->0x8006BEC8
	8006be90: bl	->0x80224BC4
	8006be94: lfs	f0, 0x00C0 (r31)
	8006be98: fcmpo	cr0,f0,f1
	8006be9c: cror	2, 0, 2
	8006bea0: bne-	 ->0x8006BF28
	8006bea4: bl	->0x80224BC4
	8006bea8: lfs	f0, 0x00B4 (r31)
	8006beac: fcmpo	cr0,f0,f1
	8006beb0: ble-	 ->0x8006BF28
	8006beb4: lbz	r0, 0x2225 (r31)
	8006beb8: li	r3, 0
	8006bebc: rlwimi	r0, r3, 7, 24, 24 (00000001)
	8006bec0: stb	r0, 0x2225 (r31)
	8006bec4: b	->0x8006BF28
	8006bec8: lbz	r0, 0x222A (r31)
	8006becc: rlwinm.	r0, r0, 26, 31, 31 (00000040)
	8006bed0: bne-	 ->0x8006BF28
	8006bed4: lbz	r0, 0x2228 (r31)
	8006bed8: rlwinm.	r0, r0, 30, 31, 31 (00000004)
	8006bedc: bne-	 ->0x8006BF28
	8006bee0: bl	->0x80224B98
	8006bee4: lfs	f0, 0x00C0 (r31)
	8006bee8: fcmpo	cr0,f0,f1
	8006beec: cror	2, 1, 2
	8006bef0: bne-	 ->0x8006BF28
	8006bef4: bl	->0x80224B98
	8006bef8: lfs	f0, 0x00B4 (r31)
	8006befc: fcmpo	cr0,f0,f1
	8006bf00: bge-	 ->0x8006BF28
	8006bf04: addi	r3, r31, 0
	8006bf08: li	r4, 96
	8006bf0c: li	r5, 127
	8006bf10: li	r6, 64
	8006bf14: bl	->0x80088148
	8006bf18: lbz	r0, 0x2225 (r31)
	8006bf1c: li	r3, 1
	8006bf20: rlwimi	r0, r3, 7, 24, 24 (00000001)
	8006bf24: stb	r0, 0x2225 (r31)
	8006bf28: lfs	f1, 0x18A4 (r31)
	8006bf2c: lfs	f0, -0x778C (rtoc)
	8006bf30: fcmpu	cr0,f1,f0
	8006bf34: beq-	 ->0x8006BF5C
	8006bf38: lbz	r0, 0x221C (r31)
	8006bf3c: rlwinm.	r0, r0, 31, 31, 31 (00000002)
	8006bf40: bne-	 ->0x8006BF5C
	8006bf44: lfs	f1, 0x00B0 (r31)
	8006bf48: bl	->0x80322258
	8006bf4c: cmpwi	r3, 0
	8006bf50: bne-	 ->0x8006BF5C
	8006bf54: lfs	f0, -0x778C (rtoc)
	8006bf58: stfs	f0, 0x18A4 (r31)
	8006bf5c: mr	r3, r28
	8006bf60: bl	->0x8007AF28
	8006bf64: lwz	r0, -0x6C98 (r13)
	8006bf68: cmpwi	r0, 3
	8006bf6c: blt-	 ->0x8006C0D4
	8006bf70: lfs	f0, 0x00B0 (r31) ------------------
	8006bf74: lis	r0, 0x7F80
	8006bf78: stfs	f0, 0x0018 (sp)
	8006bf7c: lwz	r4, 0x0018 (sp)
	8006bf80: rlwinm	r3, r4, 0, 1, 8 (7f800000)
	8006bf84: cmpw	r3, r0
	8006bf88: beq-	 ->0x8006BF9C
	8006bf8c: bge-	 ->0x8006BFCC
	8006bf90: cmpwi	r3, 0
	8006bf94: beq-	 ->0x8006BFB4
	8006bf98: b	->0x8006BFCC
	8006bf9c: rlwinm.	r0, r4, 0, 9, 31 (007fffff)
	8006bfa0: beq-	 ->0x8006BFAC
	8006bfa4: li	r0, 1
	8006bfa8: b	->0x8006BFD0
	8006bfac: li	r0, 2
	8006bfb0: b	->0x8006BFD0
	8006bfb4: rlwinm.	r0, r4, 0, 9, 31 (007fffff)
	8006bfb8: beq-	 ->0x8006BFC4
	8006bfbc: li	r0, 5
	8006bfc0: b	->0x8006BFD0
	8006bfc4: li	r0, 3
	8006bfc8: b	->0x8006BFD0
	8006bfcc: li	r0, 4
	8006bfd0: cmpwi	r0, 1
	8006bfd4: beq-	 ->0x8006C0A8
	8006bfd8: lfs	f0, 0x00B4 (r31)
	8006bfdc: lis	r0, 0x7F80
	8006bfe0: stfs	f0, 0x0014 (sp)
	8006bfe4: lwz	r4, 0x0014 (sp)
	8006bfe8: rlwinm	r3, r4, 0, 1, 8 (7f800000)
	8006bfec: cmpw	r3, r0
	8006bff0: beq-	 ->0x8006C004
	8006bff4: bge-	 ->0x8006C034
	8006bff8: cmpwi	r3, 0
	8006bffc: beq-	 ->0x8006C01C
	8006c000: b	->0x8006C034
	8006c004: rlwinm.	r0, r4, 0, 9, 31 (007fffff)
	8006c008: beq-	 ->0x8006C014
	8006c00c: li	r0, 1
	8006c010: b	->0x8006C038
	8006c014: li	r0, 2
	8006c018: b	->0x8006C038
	8006c01c: rlwinm.	r0, r4, 0, 9, 31 (007fffff)
	8006c020: beq-	 ->0x8006C02C
	8006c024: li	r0, 5
	8006c028: b	->0x8006C038
	8006c02c: li	r0, 3
	8006c030: b	->0x8006C038
	8006c034: li	r0, 4
	8006c038: cmpwi	r0, 1
	8006c03c: beq-	 ->0x8006C0A8
	8006c040: lfs	f0, 0x00B8 (r31)
	8006c044: lis	r0, 0x7F80
	8006c048: stfs	f0, 0x0010 (sp)
	8006c04c: lwz	r4, 0x0010 (sp)
	8006c050: rlwinm	r3, r4, 0, 1, 8 (7f800000)
	8006c054: cmpw	r3, r0
	8006c058: beq-	 ->0x8006C06C
	8006c05c: bge-	 ->0x8006C09C
	8006c060: cmpwi	r3, 0
	8006c064: beq-	 ->0x8006C084
	8006c068: b	->0x8006C09C
	8006c06c: rlwinm.	r0, r4, 0, 9, 31 (007fffff)
	8006c070: beq-	 ->0x8006C07C
	8006c074: li	r0, 1
	8006c078: b	->0x8006C0A0
	8006c07c: li	r0, 2
	8006c080: b	->0x8006C0A0
	8006c084: rlwinm.	r0, r4, 0, 9, 31 (007fffff)
	8006c088: beq-	 ->0x8006C094
	8006c08c: li	r0, 5
	8006c090: b	->0x8006C0A0
	8006c094: li	r0, 3
	8006c098: b	->0x8006C0A0
	8006c09c: li	r0, 4
	8006c0a0: cmpwi	r0, 1
	8006c0a4: bne-	 ->0x8006C0D4
	8006c0a8: lis	r3, 0x803C
	8006c0ac: lfs	f1, 0x00B0 (r31)
	8006c0b0: lfs	f2, 0x00B4 (r31)
	8006c0b4: addi	r3, r3, 1452
	8006c0b8: crset	6, 6
	8006c0bc: bl	->0x803456A8
	8006c0c0: lis	r3, 0x803C
	8006c0c4: addi	r3, r3, 1404
	8006c0c8: li	r4, 2517
	8006c0cc: subi	r5, r13, 31888
	8006c0d0: bl	->0x80388220
	8006c0d4: lmw	r26, 0x0068 (sp)
	8006c0d8: lwz	r0, 0x0094 (sp)
	8006c0dc: lfd	f31, 0x0088 (sp)
	8006c0e0: lfd	f30, 0x0080 (sp)
	8006c0e4: addi	sp, sp, 144
	8006c0e8: mtlr	r0
	8006c0ec: blr

fn StageInfo_CrowdGaspHeight?@80224bc4() -> float@f1
@Note:
	Only called from PlayerThink_Physics@8006b82c.
@Returns:
	The height where the crowd begins to gasp when someone falls below it and then gets above again?
@PseudoCode:
	global Stage currentStage@0x8049e6c8 # = 0x804A0000 - 6456
	# the float at pData+0x14 is also accessed by StageInfo_CameraLimitTop_Load@80224a80
	float soundTriggerDelta = currentStage.crowdReactStart@0x14 # crowdReactStart is a bit of a misnomer
	float camBot   = currentStage.cam_BottomBound@0xC
	float blastBot = currentStage.blastzoneBottom@0x80
	# compute (0.25*blastBot+ 0.75*camBot) + soundTriggerDelta (in a convoluted way), then return it.
	# The expression in the paranthesis is just a linear interpolation between blastBot and camBot,
	# then the crowdReactStart offset (which is 9 on Dreamland) is added to that.
	# The factor 0.5 comes from TOC.float@-0x3D0C, assumed to be constant.
	return 0.5*(0.5*((camBot + soundTriggerDelta) + (blastBot+soundTriggerDelta)) + (camBot+soundTriggerDelta))
@Assembly:
	80224bc4: lis	r3, 0x804A
	80224bc8: lfs	f2, -0x3D0C (rtoc)
	80224bcc: subi	r3, r3, 6456
	80224bd0: lfs	f3, 0x0014 (r3)
	80224bd4: lfs	f1, 0x000C (r3)
	80224bd8: lfs	f0, 0x0080 (r3)
	80224bdc: fadds	f1,f1,f3
	80224be0: fadds	f0,f0,f3
	80224be4: fadds	f0,f1,f0
	80224be8: fmuls	f0,f2,f0
	80224bec: fadds	f0,f1,f0
	80224bf0: fmuls	f1,f2,f0
	80224bf4: blr

fn StageInfo_OffscreenBottomLoad@80224b98() -> float@f1
@Note:
	Only called from PlayerThink_Physics@8006b82c.
@Pseudocode:
	global Stage currentStage@0x8049e6c8 # = 0x804A0000 - 6456
	# the float at pData+0x14 is also accessed by StageInfo_CameraLimitTop_Load@80224a80
	float soundTriggerDelta = currentStage.crowdReactStart@0x14 # crowdReactStart is a bit of a misnomer
	float camBot   = currentStage.cam_BottomBound@0xC
	float blastBot = currentStage.blastzoneBottom@0x80
	# The factor 0.5 comes from TOC.float@-0x3D0C, assumed to be constant.
	return 0.5 * ((camBot + soundTriggerDelta) + (blastBot+soundTriggerDelta)) # = 0.5*(camBot+blastBot) + soundTriggerDelta
@Assembly:
	80224b98: lis	r3, 0x804A
	80224b9c: lfs	f2, -0x3D0C (rtoc)
	80224ba0: subi	r3, r3, 6456
	80224ba4: lfs	f3, 0x0014 (r3)
	80224ba8: lfs	f1, 0x000C (r3)
	80224bac: lfs	f0, 0x0080 (r3)
	80224bb0: fadds	f1,f1,f3
	80224bb4: fadds	f0,f0,f3
	80224bb8: fadds	f0,f1,f0
	80224bbc: fmuls	f1,f2,f0
	80224bc0: blr

fn PositionXBetweenLedgesMinDelta@0x80322258(float characterPosX@f1)->bool@r3 # return 0 or 1
@Notes:
	Only called from PlayerThink_Physics, and even there only once.
@PseudoAssembly:
	# the struct at 0x80458868 that is used below is undocumented. Probably something stage or camera related.
	# The first values on Yoshi's Story are:
	# 0x00:  10000.0f
	# 0x04: -10000.0f
	# 0x08: -10000.0f
	# 0x0C:  10000.0f
	# 0x10:     42.0f # top platform height
	# 0x14:     -3.5f # lowest ground height, where the slope goes down
	# 0x18:    -59.5f # left side platform border. ground extends to -56.0
	# 0x1C:     59.5f # right side platform border. ground extends to 56.0
	# The first values on Fountain of Dreams are:
	# 0x00:  10000.0f
	# 0x04: -10000.0f
	# 0x08: -10000.0f
	# 0x0C:  10000.0f
	# 0x10:     42.75f     # top platform height
	# 0x14:      0.002775f # ground height
	# 0x18:    -63.3475f   # right ledge X
	# 0x1C:     63.3475f   # left ledge X
	# The first values on Pokemon Stadium are:
	# 0x00:  10000.0f
	# 0x04: -10000.0f
	# 0x08: -10000.0f
	# 0x0C:  10000.0f
	# 0x10:     25.0f  # top platform height
	# 0x14:      0.0f  # ground height
	# 0x18:    -87.75f # left ledge X
	# 0x1C:     87.75f # right ledge X
	# The first values on Battlefield are:
	# 0x00:  10000.0f
	# 0x04: -10000.0f
	# 0x08: -10000.0f
	# 0x0C:  10000.0f
	# 0x10:     54.4f # top platform height
	# 0x14:      0.0f # ground height
	# 0x18:    -68.4f # left ledge X
	# 0x1C:     68.4f # right ledge X
	# The first values on Final Destination are:
	# 0x00:  10000.0f
	# 0x04: -10000.0f
	# 0x08: -10000.0f
	# 0x0C:  10000.0f
	# 0x10:      0.0f # ground height
	# 0x14:      0.5f # ?
	# 0x18:    -85.5657f # left ledge X
	# 0x1C:     85.5657f # right ledge X
	# The first values on Dreamland are:
	# 0x00:  10000.0f
	# 0x04: -10000.0f
	# 0x08: -10000.0f
	# 0x0C:  10000.0f
	# 0x10:     51.4253f # top platform height
	# 0x14:      0.0088f # ground height
	# 0x18:    -77.2713f # left ledge X
	# 0x1C:     77.2713f # right ledge X
	# Then only zeros for a very long time, then garbage or something unrelated?
	
	global UnkStageData unkStageData@0x80458868 # = 0x80460000 - 30616
	float delta@f2 = (r13.void*@-0x51A0).float@0x2C # TODO: research where this points to
	# On Fountain: delta = 15 (Peach vs Donkey Kong)
	return unkStageData.float@0x18 + delta@f2 < characterPosX@f1 <= unkStageData.approxRightLedge(float)@0x1C - delta@f2
@Assembly:
	80322258: lwz	r4, -0x51A0 (r13)
	8032225c: lis	r3, 0x8046
	80322260: subi	r3, r3, 30616
	80322264: lfs	f2, 0x002C (r4)
	80322268: lfs	f0, 0x0018 (r3)
	8032226c: fadds	f0,f2,f0
	80322270: fcmpo	cr0,f1,f0
	80322274: blt-	 ->0x80322288
	80322278: lfs	f0, 0x001C (r3)
	8032227c: fsubs	f0,f0,f2
	80322280: fcmpo	cr0,f1,f0
	80322284: ble-	 ->0x80322290
	80322288: li	r3, 1
	8032228c: blr
	80322290: li	r3, 0
	80322294: blr

fn FtChkDevice_DecrementImmunity@0x800c0a98(PlayerEntityStruct* pPlayerEntityStruct@r3)->void
@Reimplementation:
	CharData* pCharData@r4 = pPlayerEntityStruct@r3.pCharData@0x2C
	
	# community spreadsheet on 0x2328: Directly related to Hitbox.0x04. When creating a hitbox, if what that value gets set to is equal to the value in this memory address, it will trigger a function that copies unknown parts of the hitbox.See @0x800768a0
	if pCharData@r4.hitboxInt?@0x2328 != 0:
		pCharData@r4.hitboxInt?@0x2328 -= 1
	
	# community spreadsheet on 0x2324: Appears to be a value or duration of sorts. See @0x800768a0
	if pCharData@r4.int@0x2324 is_element_of [4, 8, 30, 32, 39]:
		if pCharData@r4.int@0x232C != 0: # undocumented member. All 3 integers that were used by this function are directly next to each other in memory.
			pCharData@r4.int@0x232C -= 1
@PseudoAssembly:
	CharData* pCharData@r4 = pPlayerEntityStruct@r3.pCharData@0x2C
	
	# The community spreadsheet tells us this about 0x2328:
	# Directly related to Hitbox.0x04. When creating a hitbox, if what that value gets set to is equal to the value in this memory address, it will trigger a function that copies unknown parts of the hitbox.See @0x800768a0
	int hitboxInt?@r3 = pCharData@r4.hitboxInt?@0x2328
	
	if pCharData@r4.hitboxInt?@0x2328 != 0:
		pCharData@r4.int@0x2328 -= 1
	
	# spreadsheet about 0x2324: Appears to be a value or duration of sorts. See @0x800768a0
	r0 = pCharData@r4.int@0x2324
	if r0 != 30:
		if r0 < 30:
			if r0 == 8: goto JC1@0x800C0B08
			if r0 >= 8: return
			if r0 == 4: goto JC2@0x800C0AF0
			return
		if r0 == 39: goto JC1@0x800C0B08
		if r0 >= 39: return
		if r0 == 32: goto JC1@0x800C0B08
		return
	JC2:
	if pCharData@r4.int@0x232C != 0: # undocumented member
		pCharData@r4.int@0x232C -= 1
	return
	
	JC1:
	if pCharData@r4.int@0x232C != 0:
		pCharData@r4.int@0x232C -= 1
	return
@Assembly:
	800c0a98: lwz	r4, 0x002C (r3)
	800c0a9c: lwz	r3, 0x2328 (r4)
	800c0aa0: cmplwi	r3, 0
	800c0aa4: beq-	 ->0x800C0AB0
	800c0aa8: subi	r0, r3, 1
	800c0aac: stw	r0, 0x2328 (r4)
	800c0ab0: lwz	r0, 0x2324 (r4)
	800c0ab4: cmpwi	r0, 30
	800c0ab8: beq-	 ->0x800C0AF0
	800c0abc: bge-	 ->0x800C0AD8
	800c0ac0: cmpwi	r0, 8
	800c0ac4: beq-	 ->0x800C0B08
	800c0ac8: bgelr-
	800c0acc: cmpwi	r0, 4
	800c0ad0: beq-	 ->0x800C0AF0
	800c0ad4: blr
	800c0ad8: cmpwi	r0, 39
	800c0adc: beq-	 ->0x800C0B08
	800c0ae0: bgelr-
	800c0ae4: cmpwi	r0, 32
	800c0ae8: beq-	 ->0x800C0B08
	800c0aec: blr
	800c0af0: lwz	r3, 0x232C (r4)
	800c0af4: cmplwi	r3, 0
	800c0af8: beqlr-
	800c0afc: subi	r0, r3, 1
	800c0b00: stw	r0, 0x232C (r4)
	800c0b04: blr	
	800c0b08: lwz	r3, 0x232C (r4)
	800c0b0c: cmplwi	r3, 0
	800c0b10: beqlr-
	800c0b14: subi	r0, r3, 1
	800c0b18: stw	r0, 0x232C (r4)
	800c0b1c: blr

fn Stage_CheckForWindHazards@8007b924(PlayerEntityStruct* pPlayerEntityStruct@r3, Vec3* pResultVec@r4)->void
@PseudoAssembly:
	# save lr, r1, r27..r31 on the stack, remaining stack size is 0x24
	
	pPlayerEntityStruct@r27 = pPlayerEntityStruct@r3
	pResultVec@r28 = pResultVec@r4
	
	CharData* pCharData@r3 = pPlayerEntityStruct@r3.pCharData@0x2C
	
	*pResultVec@r4 = vec3(0) # = vec3(TOC.float@-0x7700), I think this is always vec3(0.0f)
	
	# TODO: the documented bitflags are: 1 = can walljump, 0x10 = HP Flag, 0x20 = Stamina Alive. The tested bit is not documented.
	if pCharData@r3@.bitflags(byte)0x2224.bits[3] == 0: # bits[0] = least significant bit
		# r31 = 0x80460000 - 26008
		for(r30 = 0, void* pData@r31 = 0x80459A68; r30 <= *(int32)(r13 - 0x5128); r30 += 1, pData@r31 += 12):
			int dataVal@r0 = pData@r31.int32@0x0
			dataVal@r29 = dataVal@r0
			if dataVal@r0 == 0:
				continue
			
			# This code block has no effect:
			# The result of the result is always 1, 2 or 3 => continue not reached, and FtChkDevice_CheckIfVuln has no side effects.
			if (!FtChkDevice_CheckIfVuln@0x800C0A28(r3 = pPlayerEntityStruct@r27, /*unused argument*/r4 = dataVal@r29, r5 = pData@r31.int32@0x4)):
				continue
			
			vec3 resultVec@sp0x14
			(pData@r31.unkFuncPtr@0x8)(r3 = dataVal@r29, r4 = pPlayerEntityStruct@r27, r5 = @resultVec@sp0x14)
			if r3 == 0:
				continue
			*pResultVec@r28 += resultVec@sp0x14
	# unwind stack and return
@Assembly:
	8007b924: mflr	r0
	8007b928: stw	r0, 0x0004 (sp)
	8007b92c: stwu	sp, -0x0038 (sp)
	8007b930: stmw	r27, 0x0024 (sp)
	8007b934: mr	r27, r3
	8007b938: mr	r28, r4
	8007b93c: lfs	f0, -0x7700 (rtoc)
	8007b940: lwz	r3, 0x002C (r3)
	8007b944: stfs	f0, 0x0008 (r4)
	8007b948: stfs	f0, 0x0004 (r4)
	8007b94c: stfs	f0, 0 (r4)
	8007b950: lbz	r0, 0x2224 (r3)
	8007b954: rlwinm.	r0, r0, 29, 31, 31 (00000008)
	8007b958: bne-	 ->0x8007B9F8
	8007b95c: lis	r3, 0x8046
	8007b960: subi	r31, r3, 26008
	8007b964: li	r30, 0
	8007b968: b	->0x8007B9EC
	8007b96c: lwz	r0, 0 (r31)
	8007b970: cmplwi	r0, 0
	8007b974: mr	r29, r0
	8007b978: beq-	 ->0x8007B9E4
	8007b97c: lwz	r5, 0x0004 (r31)
	8007b980: addi	r3, r27, 0
	8007b984: addi	r4, r29, 0
	8007b988: bl	->0x800C0A28
	8007b98c: cmpwi	r3, 0
	8007b990: beq-	 ->0x8007B9E4
	8007b994: lwz	r12, 0x0008 (r31)
	8007b998: addi	r3, r29, 0
	8007b99c: addi	r4, r27, 0
	8007b9a0: mtlr	r12
	8007b9a4: addi	r5, sp, 20
	8007b9a8: blrl	
	8007b9ac: cmpwi	r3, 0
	8007b9b0: beq-	 ->0x8007B9E4
	8007b9b4: lfs	f1, 0 (r28)
	8007b9b8: lfs	f0, 0x0014 (sp)
	8007b9bc: fadds	f0,f1,f0
	8007b9c0: stfs	f0, 0 (r28)
	8007b9c4: lfs	f1, 0x0004 (r28)
	8007b9c8: lfs	f0, 0x0018 (sp)
	8007b9cc: fadds	f0,f1,f0
	8007b9d0: stfs	f0, 0x0004 (r28)
	8007b9d4: lfs	f1, 0x0008 (r28)
	8007b9d8: lfs	f0, 0x001C (sp)
	8007b9dc: fadds	f0,f1,f0
	8007b9e0: stfs	f0, 0x0008 (r28)
	8007b9e4: addi	r31, r31, 12
	8007b9e8: addi	r30, r30, 1
	8007b9ec: lwz	r0, -0x5128 (r13)
	8007b9f0: cmpw	r30, r0
	8007b9f4: blt+	 ->0x8007B96C
	8007b9f8: lmw	r27, 0x0024 (sp)
	8007b9fc: lwz	r0, 0x003C (sp)
	8007ba00: addi	sp, sp, 56
	8007ba04: mtlr	r0
	8007ba08: blr


fn FtChkDevice_CheckIfVuln@0x800c0a28(PlayerEntityStruct*  pPlayerEntityStruct@r3, r4: __unused, int intArg@r5) -> bool@r3 # 0 = false, 1 = true
@CalledBy:
	Stage_CheckForWindHazards@8007b924
	...?
@PseudoAssembly:
	CharData* pCharData@r3 = pPlayerEntityStruct@r3.pCharData@0x2C
	if intArg@r5 == 3:
		# The next ASM code is:
		# if r5 >= 3: return 1
		# if r5 < 2: return 1
		# this is of course:
		if intArg@r5 != 2:
			return True
		if pCharData@r3.unkInt32@0x232C != 0 || # undocumented property
		   pCharData@r3.actionState(int32)@0x0010 == 293 || # Action state 293 = BarrelWait
		   pCharData@r3.grabFlags(int16)@0x1A6A.bits[5] || # bit[0] = least significant bit
		   pCharData@r3.bitflags(byte)@0x2224.bits[5]: # bits[0]=least significant bit. bits[5] is not documented, also used in Stage_CheckForWindHazards
			return False
		return True
	return pCharData@r3.unkInt32@0x232C == 0 # this property was tested a few lines before too
@Assembly:
	800c0a28: cmpwi	r5, 3
	800c0a2c: lwz	r3, 0x002C (r3)
	800c0a30: beq-	 ->0x800C0A7C
	800c0a34: bge-	 ->0x800C0A90
	800c0a38: cmpwi	r5, 2
	800c0a3c: bge-	 ->0x800C0A44
	800c0a40: b	->0x800C0A90
	800c0a44: lwz	r0, 0x232C (r3)
	800c0a48: cmplwi	r0, 0
	800c0a4c: bne-	 ->0x800C0A74
	800c0a50: lwz	r0, 0x0010 (r3)
	800c0a54: cmpwi	r0, 293
	800c0a58: beq-	 ->0x800C0A74
	800c0a5c: lhz	r0, 0x1A6A (r3)
	800c0a60: rlwinm.	r0, r0, 0, 26, 26 (00000020)
	800c0a64: bne-	 ->0x800C0A74
	800c0a68: lbz	r0, 0x2224 (r3)
	800c0a6c: rlwinm.	r0, r0, 27, 31, 31 (00000020)
	800c0a70: beq-	 ->0x800C0A90
	800c0a74: li	r3, 0
	800c0a78: blr
	800c0a7c: lwz	r0, 0x232C (r3)
	800c0a80: cmplwi	r0, 0
	800c0a84: beq-	 ->0x800C0A90
	800c0a88: li	r3, 0
	800c0a8c: blr
	800c0a90: li	r3, 1
	800c0a94: blr

fn SetAccelAndSelfVelVectors@0x8007cb74(PlayerEntityStruct* pPlayerEntityStruct@r3) -> void
@Callstack:
	Physics_Friction 80084f78
	Physics_Wait 8008a658
	PlayerThink_Physics 8006b8ac
	GObjProc 80390dfc
	updateFunction 801a4fa0
	Scene_ProcessMinor 801a40f0
	Scene_ProcessMajor 801a44c0
	Scene_Main 801a45c4
	main 801601a8
@ReturnValues:
	possibly r3 = pPlayerEntityStruct@r3.pCharData@0x2C is returned, because r3 is not used after the assignment.
	But probably the compiler just didn't optimize that away.
@PseudoAssembly:
	# save r30, r31 on the stackframe
	CharData* pCharData@r30 = pPlayerEntityStruct@r3.pCharData@0x2C
	
	Vec3* pNormal@r31 = &pCharData@r30.surfaceNormal@0x844
	
	float frictionMult@f1 = Stage_GetGroundFrictionMultiplier@0x80084A40(r3 = pCharData@r30) # TODO: rename Stage_GetGroundFrictionMultiplier because it also applies to groundAccel1. Stage_GetGroundSlipperiness?
	#8007cb98
	if frictionMult@f1 < 1: # 1 = TOC@r2.float@-0x76AC
		#8007cba4
		pCharData@r30.groundAccel1@0xE4 *= frictionMult@f1
	
	#8007cbb0
	pCharData@r30.accel@0x74.xy = pCharData@r30.groundAccel1@0xE4.x * vec2(pNormal@r31.y, -pNormal@r31.x)
	pCharData@r30.accel@0x74.z = 0 # = 0.0f@TOC-0x76B0
	
	#8007cbdc update velocity vector
	pCharData@r30.self_vel@0x80.xy = pCharData@r30.groundVel@0xEC * vec2(pNormal@r31.y, -pNormal@r31.x)
	pCharData@r30.self_vel@0x80.z = 0 # = 0.0f@TOC-0x76B0
	
	# unwind stackframe and return
@Assembly:
	8007cb74: mflr	r0
	8007cb78: stw	r0, 0x0004 (sp)
	8007cb7c: stwu	sp, -0x0020 (sp)
	8007cb80: stw	r31, 0x001C (sp)
	8007cb84: stw	r30, 0x0018 (sp)
	8007cb88: lwz	r30, 0x002C (r3)
	8007cb8c: addi	r3, r30, 0
	8007cb90: addi	r31, r30, 2116
	8007cb94: bl	->0x80084A40
	8007cb98: lfs	f0, -0x76AC (rtoc)
	8007cb9c: fcmpo	cr0,f1,f0
	8007cba0: bge-	 ->0x8007CBB0
	8007cba4: lfs	f0, 0x00E4 (r30)
	8007cba8: fmuls	f0,f0,f1
	8007cbac: stfs	f0, 0x00E4 (r30)
	8007cbb0: lfs	f1, 0x0004 (r31)
	8007cbb4: lfs	f0, 0x00E4 (r30)
	8007cbb8: fmuls	f0,f1,f0
	8007cbbc: stfs	f0, 0x0074 (r30)
	8007cbc0: lfs	f1, 0 (r31)
	8007cbc4: lfs	f0, 0x00E4 (r30)
	8007cbc8: fneg	f1,f1
	8007cbcc: fmuls	f0,f1,f0
	8007cbd0: stfs	f0, 0x0078 (r30)
	8007cbd4: lfs	f2, -0x76B0 (rtoc)
	8007cbd8: stfs	f2, 0x007C (r30)
	8007cbdc: lfs	f1, 0x0004 (r31)
	8007cbe0: lfs	f0, 0x00EC (r30)
	8007cbe4: fmuls	f0,f1,f0
	8007cbe8: stfs	f0, 0x0080 (r30)
	8007cbec: lfs	f1, 0 (r31)
	8007cbf0: lfs	f0, 0x00EC (r30)
	8007cbf4: fneg	f1,f1
	8007cbf8: fmuls	f0,f1,f0
	8007cbfc: stfs	f0, 0x0084 (r30)
	8007cc00: stfs	f2, 0x0088 (r30)
	8007cc04: lwz	r0, 0x0024 (sp)
	8007cc08: lwz	r31, 0x001C (sp)
	8007cc0c: lwz	r30, 0x0018 (sp)
	8007cc10: addi	sp, sp, 32
	8007cc14: mtlr	r0
	8007cc18: blr

fn reduceMagnitude@0x8007cd6c(float value@f1, float delta@f2)->float@f1
@Reimplementation:
	return sign(value) * max(abs(value) - delta, 0)
@PseudoAssembly:
	# we use that TOC.float@-0x76B0 = 0
	if f1 > 0:
		f1 -= f2
		if f1 >= 0:
			return f1
		f1 = 0
		return f1
	if f1 >= 0:
		return f1
	f1 += f2
	if f1 <= 0:
		return f1
	f1 = 0
	return f1
@Assembly:
	8007cd6c: lfs	f0, -0x76B0 (rtoc)
	8007cd70: fcmpo	cr0,f1,f0
	8007cd74: ble-	 ->0x8007CD8C
	8007cd78: fsubs	f1,f1,f2
	8007cd7c: fcmpo	cr0,f1,f0
	8007cd80: bgelr-
	8007cd84: fmr	f1, f0
	8007cd88: blr
	8007cd8c: bgelr-
	8007cd90: fadds	f1,f1,f2
	8007cd94: fcmpo	cr0,f1,f0
	8007cd98: blelr-
	8007cd9c: fmr	f1, f0
	8007cda0: blr

fn reduceGroundKnockbackVel@8007cca0(CharData* pCharData@r3, float delta@f1)
@Reimplementation:
	pCharData.ground_kb_vel = reduceMagnitude@0x8007cd6c(pCharData.ground_kb_vel, delta)
@PseudoAssembly:
	if pCharData@r3.ground_kb_vel@0xF0 < 0:
		pCharData@r3.ground_kb_vel@0xF0 += delta@f1
		if pCharData@r3.ground_kb_vel@0xF0 > 0:
			pCharData@r3.ground_kb_vel@0xF0 = 0
		return
	pCharData@r3.ground_kb_vel@0xF0 -= delta@f1
	if pCharData@r3.ground_kb_vel@0xF0 < 0:
		pCharData@r3.ground_kb_vel@0xF0 = 0
@Assembly:
	8007cca0: lfs	f0, 0x00F0 (r3)
	8007cca4: lfs	f2, -0x76B0 (rtoc)
	8007cca8: fcmpo	cr0,f0,f2
	8007ccac: bge-	 ->0x8007CCCC
	8007ccb0: fadds	f0,f0,f1
	8007ccb4: stfs	f0, 0x00F0 (r3)
	8007ccb8: lfs	f0, 0x00F0 (r3)
	8007ccbc: fcmpo	cr0,f0,f2
	8007ccc0: blelr-
	8007ccc4: stfs	f2, 0x00F0 (r3)
	8007ccc8: blr
	8007cccc: fsubs	f0,f0,f1
	8007ccd0: stfs	f0, 0x00F0 (r3)
	8007ccd4: lfs	f0, 0x00F0 (r3)
	8007ccd8: fcmpo	cr0,f0,f2
	8007ccdc: bgelr-
	8007cce0: stfs	f2, 0x00F0 (r3)
	8007cce4: blr

fn reduceGroundShieldKnockbackVel@0x8007ce4c(CharData* pCharData@r3, float delta@f1)
@Reimplementation:
	pCharData.ground_shield_kb_vel = reduceMagnitude@0x8007cd6c(pCharData.ground_shield_kb_vel, delta)
@AssemblyPseudocode:
	f0 = pCharData@r3.ground_shield_kb_vel@0xF4
	if f0 < 0:
		f0 += f1
		pCharData@r3.ground_shield_kb_vel@0xF4 = f0
		if f0 <= 0:
			return
		pCharData@r3.ground_shield_kb_vel@0xF4 = 0
		return
	f0 -= f1
	pCharData@r3.ground_shield_kb_vel@0xF4 = f0
	if f0 >= 0:
		return
	pCharData@r3.ground_shield_kb_vel@0xF4 = 0
@Assembly:
	8007ce4c: lfs	f0, 0x00F4 (r3)
	8007ce50: lfs	f2, -0x76B0 (rtoc)
	8007ce54: fcmpo	cr0,f0,f2
	8007ce58: bge-	 ->0x8007CE78
	8007ce5c: fadds	f0,f0,f1
	8007ce60: stfs	f0, 0x00F4 (r3)
	8007ce64: lfs	f0, 0x00F4 (r3)
	8007ce68: fcmpo	cr0,f0,f2
	8007ce6c: blelr-
	8007ce70: stfs	f2, 0x00F4 (r3)
	8007ce74: blr
	8007ce78: fsubs	f0,f0,f1
	8007ce7c: stfs	f0, 0x00F4 (r3)
	8007ce80: lfs	f0, 0x00F4 (r3)
	8007ce84: fcmpo	cr0,f0,f2
	8007ce88: bgelr-
	8007ce8c: stfs	f2, 0x00F4 (r3)
	8007ce90: blr

fn Collision_GetPositionDifference@0x800567c0(uint groundID@r3, Vec3* fighterPos@r4, Vec3* UnkReturnVector@r5) -> r3=1 ?
@Notes:
	sets r3=1 just before returning, without using r1 again. Is that a constant return value = 1?
@Assembly:
	800567c0: mflr	r0
	800567c4: cmpwi	r3, -1
	800567c8: stw	r0, 0x0004 (sp)
	800567cc: lis	r6, 0x803C
	800567d0: stwu	sp, -0x0038 (sp)
	800567d4: stw	r31, 0x0034 (sp)
	800567d8: subi	r31, r6, 11304
	800567dc: stw	r30, 0x0030 (sp)
	800567e0: addi	r30, r5, 0
	800567e4: stw	r29, 0x002C (sp)
	800567e8: addi	r29, r4, 0
	800567ec: bne-	 ->0x800567F8
	800567f0: li	r0, 0
	800567f4: b	->0x80056858
	800567f8: cmpwi	r3, 0
	800567fc: blt-	 ->0x80056810
	80056800: lwz	r4, -0x51EC (r13)
	80056804: lwz	r0, 0x000C (r4)
	80056808: cmpw	r3, r0
	8005680c: blt-	 ->0x8005682C
	80056810: addi	r6, r3, 0
	80056814: crclr	6, 6
	80056818: addi	r3, r31, 8408
	8005681c: subi	r4, r13, 32072
	80056820: li	r5, 4636
	80056824: bl	OSReport@0x803456A8
	80056828: b	->0x80056828
	8005682c: lwz	r4, -0x51E4 (r13)
	80056830: rlwinm	r0, r3, 3, 0, 28 (1fffffff)
	80056834: add	r4, r4, r0
	80056838: lwz	r4, 0x0004 (r4)
	8005683c: rlwinm.	r0, r4, 0, 15, 15 (00010000)
	80056840: beq-	 ->0x8005684C
	80056844: rlwinm.	r0, r4, 0, 13, 13 (00040000)
	80056848: beq-	 ->0x80056854
	8005684c: li	r0, 0
	80056850: b	->0x80056858
	80056854: li	r0, 1
	80056858: cmpwi	r0, 0
	8005685c: bne-	 ->0x80056868
	80056860: li	r3, 0
	80056864: b	->0x800569D0
	80056868: lwz	r4, -0x51E4 (r13)
	8005686c: rlwinm	r0, r3, 3, 0, 28 (1fffffff)
	80056870: lwz	r7, -0x51E8 (r13)
	80056874: addi	r3, sp, 32
	80056878: lwzx	r6, r4, r0
	8005687c: lfs	f0, 0 (r29)
	80056880: addi	r4, sp, 28
	80056884: lhz	r5, 0 (r6)
	80056888: lhz	r0, 0x0002 (r6)
	8005688c: mulli	r5, r5, 24
	80056890: stfs	f0, 0x0008 (sp)
	80056894: mulli	r0, r0, 24
	80056898: lfs	f0, 0x0004 (r29)
	8005689c: stfs	f0, 0x000C (sp)
	800568a0: add	r5, r7, r5
	800568a4: add	r6, r7, r0
	800568a8: lfs	f1, 0x0010 (r5)
	800568ac: lfs	f2, 0x0014 (r5)
	800568b0: lfs	f3, 0x0010 (r6)
	800568b4: lfs	f4, 0x0014 (r6)
	800568b8: lfs	f5, 0x0008 (r5)
	800568bc: lfs	f6, 0x000C (r5)
	800568c0: lfs	f7, 0x0008 (r6)
	800568c4: lfs	f8, 0x000C (r6)
	800568c8: bl	->0x8004DC90
	800568cc: lfs	f1, 0x0020 (sp)
	800568d0: lfs	f0, 0 (r29)
	800568d4: fsubs	f0,f1,f0
	800568d8: stfs	f0, 0 (r30)
	800568dc: lfs	f1, 0x001C (sp)
	800568e0: lfs	f0, 0x0004 (r29)
	800568e4: fsubs	f0,f1,f0
	800568e8: stfs	f0, 0x0004 (r30)
	800568ec: lfs	f0, -0x7990 (rtoc)
	800568f0: stfs	f0, 0x0008 (r30)
	800568f4: lwz	r0, -0x6C98 (r13)
	800568f8: cmpwi	r0, 3
	800568fc: blt-	 ->0x800569CC
	80056900: lfs	f1, 0 (r30)
	80056904: fcmpo	cr0,f1,f0
	80056908: bge-	 ->0x80056914
	8005690c: fneg	f2,f1
	80056910: b	->0x80056918
	80056914: fmr	f2, f1
	80056918: lfs	f0, -0x7934 (rtoc)
	8005691c: fcmpo	cr0,f2,f0
	80056920: bgt-	 ->0x80056944
	80056924: lfs	f2, 0x0004 (r30)
	80056928: lfs	f0, -0x7990 (rtoc)
	8005692c: fcmpo	cr0,f2,f0
	80056930: bge-	 ->0x80056938
	80056934: fneg	f2,f2
	80056938: lfs	f0, -0x7934 (rtoc)
	8005693c: fcmpo	cr0,f2,f0
	80056940: ble-	 ->0x800569CC
	80056944: lfs	f2, 0x0004 (r30)
	80056948: addi	r3, r31, 8436
	8005694c: crset	6, 6
	80056950: subi	r4, r13, 32072
	80056954: li	r5, 5333
	80056958: bl	->0x803456A8
	8005695c: lfs	f1, 0 (r30)
	80056960: li	r0, 1
	80056964: lfs	f0, -0x7990 (rtoc)
	80056968: fcmpo	cr0,f1,f0
	8005696c: bge-	 ->0x80056974
	80056970: fneg	f1,f1
	80056974: lfs	f0, -0x7934 (rtoc)
	80056978: fcmpo	cr0,f1,f0
	8005697c: bgt-	 ->0x800569A4
	80056980: lfs	f1, 0x0004 (r30)
	80056984: lfs	f0, -0x7990 (rtoc)
	80056988: fcmpo	cr0,f1,f0
	8005698c: bge-	 ->0x80056994
	80056990: fneg	f1,f1
	80056994: lfs	f0, -0x7934 (rtoc)
	80056998: fcmpo	cr0,f1,f0
	8005699c: bgt-	 ->0x800569A4
	800569a0: li	r0, 0
	800569a4: cmpwi	r0, 0
	800569a8: beq-	 ->0x800569BC
	800569ac: addi	r5, r31, 8476
	800569b0: subi	r3, r13, 32072
	800569b4: li	r4, 5334
	800569b8: bl	__assert@0x80388220
	800569bc: subi	r3, r13, 32072
	800569c0: li	r4, 5335
	800569c4: subi	r5, r13, 32064
	800569c8: bl	__assert@0x80388220
	800569cc: li	r3, 1
	800569d0: lwz	r0, 0x003C (sp)
	800569d4: lwz	r31, 0x0034 (sp)
	800569d8: lwz	r30, 0x0030 (sp)
	800569dc: lwz	r29, 0x002C (sp)
	800569e0: addi	sp, sp, 56
	800569e4: mtlr	r0
	800569e8: blr

fn DataOffset_ComboCount_TopNAttackerModify@0x80076528(PlayerEntityStruct* pPlayerEntityStruct@r3)->void
@PseudoAssembly:
	CharData* pCharData@r5 = pPlayerEntityStruct@r3.pCharData@0x2C
	if pCharData@r5.int16@0x2092 == 0: # undocumented member
		return
	pCharData@r5.int16@0x2092 -= 1
	
	# return if we are being grabbed or in the air?
	if (pCharData@r5.p_grabAttacker@0x1A58 != 0) or (pCharData@r5.airborne(int)@0xE0 != 0):
		return
	
	Vec3* pGroundSlope@r4 = &pCharData@r5.collisionDatta.groundSlope # = pCharData + 0x844, which points into the collision data struct, which starts at 0x6F0. The offfset into the collision data thus is 0x844-0x6F0=0x154. This is the groundSlope
	uint16 comboCounter@r3 = pCharData@r5.comboCounter(int16)@0x2090
	float f@f2 = (comboCounter@r3 < p_stc_ftcommon@(r13-0x514c).int?@0x4C8) ?
		p_stc_ftcommon@r6.float?@0x4D0 : p_stc_ftcommon@r6.float?@0x4D4
	pCharData@r5.position@0xB0.xy += pCharData@r5.facingDirection@0x2C * f@f2 * vec2(-pGroundSlope@r4.y@0x4, pGroundSlope@r4.x@0x0)
@Assembly:
	80076528: lwz	r5, 0x002C (r3)
	8007652c: lhz	r3, 0x2092 (r5)
	80076530: cmplwi	r3, 0
	80076534: beqlr-
	80076538: subi	r0, r3, 1
	8007653c: sth	r0, 0x2092 (r5)
	80076540: lwz	r0, 0x1A58 (r5)
	80076544: cmplwi	r0, 0
	80076548: bnelr-
	8007654c: lwz	r0, 0x00E0 (r5)
	80076550: cmpwi	r0, 0
	80076554: bnelr-
	80076558: lwz	r6, -0x514C (r13)
	8007655c: addi	r4, r5, 2116
	80076560: lhz	r3, 0x2090 (r5)
	80076564: lwz	r0, 0x04C8 (r6)
	80076568: cmpw	r3, r0
	8007656c: bge-	 ->0x80076578
	80076570: lfs	f2, 0x04D0 (r6)
	80076574: b	->0x8007657C
	80076578: lfs	f2, 0x04D4 (r6)
	8007657c: lfs	f0, 0x002C (r5)
	80076580: lfs	f1, 0x0004 (r4)
	80076584: fmuls	f2,f0,f2
	80076588: lfs	f0, 0x00B0 (r5)
	8007658c: fnmsubs	f0,f1,f2,f0
	80076590: stfs	f0, 0x00B0 (r5)
	80076594: lfs	f1, 0 (r4)
	80076598: lfs	f0, 0x00B4 (r5)
	8007659c: fneg	f1,f1
	800765a0: fnmsubs	f0,f1,f2,f0
	800765a4: stfs	f0, 0x00B4 (r5)
	800765a8: blr

fn getVec0x2D4_X_assertPlayerIndex@0x8007cda4(CharData* pCharData@r3) -> float@f1
@Note:
	The knockback x is decreased by this magnitude under certain conditions in PlayerThink_Physics@0x80322258.
@PseudoAssembly:
	# save lr, r1, r31 on the stack
	pCharData@r31 = pCharData@r3
	if pCharData@r3.playerIndex@0x4 != 32: # playerIndex a misnomer? Expected value is 0-4. Here it asserts for values != 32. playerIndex has value 9 in a testrun in PlayerThink_Physics.
		__assert@0x80388220(r3 = 0x803C0D58, r4 = 299, r5 = 0x803C0D64)
	return pCharData@r31.ptrTo0x2420@0x2D4.float@0x0
	# restore registers from stackframe and return
@Assembly:
	8007cda4: mflr	r0
	8007cda8: stw	r0, 0x0004 (sp)
	8007cdac: stwu	sp, -0x0018 (sp)
	8007cdb0: stw	r31, 0x0014 (sp)
	8007cdb4: mr	r31, r3
	8007cdb8: lwz	r0, 0x0004 (r3)
	8007cdbc: cmpwi	r0, 32
	8007cdc0: beq-	 ->0x8007CDDC
	8007cdc4: lis	r3, 0x803C
	8007cdc8: lis	r4, 0x803C
	8007cdcc: addi	r5, r4, 3428
	8007cdd0: addi	r3, r3, 3416
	8007cdd4: li	r4, 299
	8007cdd8: bl	->0x80388220
	8007cddc: lwz	r3, 0x02D4 (r31)
	8007cde0: lwz	r0, 0x001C (sp)
	8007cde4: lfs	f1, 0 (r3)
	8007cde8: lwz	r31, 0x0014 (sp)
	8007cdec: addi	sp, sp, 24
	8007cdf0: mtlr	r0
	8007cdf4: blr

fn getVec0x2D4_Y_assertPlayerIndex@0x8007cdf8(CharData* pCharData@r3) -> float@f1
@Note:
	The knockback y is decreased by this magnitude under certain conditions in PlayerThink_Physics@0x80322258.
@PseudoAssembly:
	# save lr, r1, r31 on the stack
	pCharData@r31 = pCharData@r3
	if pCharData@r3.playerIndex@0x4 != 32: # playerIndex a misnomer? Expected value is 0-4. Here it asserts for values != 32. playerIndex has value 9 in a testrun in PlayerThink_Physics.
		__assert@0x80388220(r3 = 0x803C0D58, r4 = 308, r5 = 0x803C0D64)
	return pCharData@r31.ptrTo0x2420@0x2D4.float@0x4
	# restore registers from stackframe and return
@Assembly:
	8007cdf8: mflr	r0
	8007cdfc: stw	r0, 0x0004 (sp)
	8007ce00: stwu	sp, -0x0018 (sp)
	8007ce04: stw	r31, 0x0014 (sp)
	8007ce08: mr	r31, r3
	8007ce0c: lwz	r0, 0x0004 (r3)
	8007ce10: cmpwi	r0, 32
	8007ce14: beq-	 ->0x8007CE30
	8007ce18: lis	r3, 0x803C
	8007ce1c: lis	r4, 0x803C
	8007ce20: addi	r5, r4, 3428
	8007ce24: addi	r3, r3, 3416
	8007ce28: li	r4, 308
	8007ce2c: bl	->0x80388220
	8007ce30: lwz	r3, 0x02D4 (r31)
	8007ce34: lwz	r0, 0x001C (sp)
	8007ce38: lfs	f1, 0x0004 (r3)
	8007ce3c: lwz	r31, 0x0014 (sp)
	8007ce40: addi	sp, sp, 24
	8007ce44: mtlr	r0
	8007ce48: blr

fn __assert@80388220(int arg1@r3, int arg2@r4, int arg3@r5) -> void
@Note:
	Probably never returns?
@PseudoAssembly:
	# save lr, r1, r30, r31 on the stack
	
	# save args to non-volatile registers before calling OSReport
	arg1@r30 = arg1@r3
	arg2@r31 = arg2@r4
	
	OSReport@0x803456A8(r3 = 0x80407D60, r4 = arg3@r5, CR.bits[6] = 0) # bit[0] is leftmost bit. Is CR used by OSReport?
	HSD_Panic@0x80388278(r3 = arg1@r30, r4 = arg2@r31, r5 = r13 - 0x5690) # r13 is a special datablock pointer like r2
	# restore registers from stackframe and return. This code is probably never reached.
@Assembly:
	80388220: mflr	r0
	80388224: stw	r0, 0x0004 (sp)
	80388228: stwu	sp, -0x0020 (sp)
	8038822c: stw	r31, 0x001C (sp)
	80388230: stw	r30, 0x0018 (sp)
	80388234: mr	r30, r3
	80388238: mr	r31, r4
	8038823c: lis	r3, 0x8040
	80388240: crclr	6, 6
	80388244: addi	r3, r3, 32096
	80388248: mr	r4, r5
	8038824c: bl	->0x803456A8
	80388250: mr	r3, r30
	80388254: mr	r4, r31
	80388258: subi	r5, r13, 22160
	8038825c: bl	->0x80388278
	80388260: lwz	r0, 0x0024 (sp)
	80388264: lwz	r31, 0x001C (sp)
	80388268: lwz	r30, 0x0018 (sp)
	8038826c: addi	sp, sp, 32
	80388270: mtlr	r0
	80388274: blr

