// Box.asm  -  Capstone Project, K = 1
// Student roll no: 2501010201   K = 01
//
// Box parameters (K = 1):
//   Start row  : 1
//   Height     : 20 rows
//   Width      : 16 x ((K mod 4) + 1) = 16 x 2 = 32 pixels = 2 words per row
//
// Screen memory map:
//   SCREEN base = 16384
//   Row r  starts at SCREEN + 32*r
//   Row 1  starts at 16384 + 32   = 16416
//   After 20 rows: end address    = 16416 + 20*32 = 17056  (exclusive)
//
// Algorithm:
//   LOOP:
//     Read keyboard.
//     If key pressed  -> draw box (color = -1) then goto LOOP
//     If no key       -> clear box (color = 0)  then goto LOOP
//
//   FILL sub-routine:
//     addr  = 16416   (start of box in screen RAM)
//     end   = 17056   (first address past the box)
//     Write color to RAM[addr] and RAM[addr+1]  (two 16-pixel words = 32px wide)
//     addr += 32      (advance one full screen row)
//     Repeat until addr >= end

// -----------------------------------------------------------------------
// LOOP: check keyboard
// -----------------------------------------------------------------------
(LOOP)
    @KBD
    D=M             // D = value at keyboard register
    @CLEAR
    D;JEQ           // if D==0 (no key), jump to CLEAR
                    // otherwise fall through to DRAW

// -----------------------------------------------------------------------
// DRAW: set color = -1 (black), then fill
// -----------------------------------------------------------------------
(DRAW)
    @color
    M=-1            // color = 1111111111111111  (black)
    @FILL
    0;JMP

// -----------------------------------------------------------------------
// CLEAR: set color = 0 (white), then fill
// -----------------------------------------------------------------------
(CLEAR)
    @color
    M=0             // color = 0000000000000000  (white)

// -----------------------------------------------------------------------
// FILL: paint 2 words per row for 20 rows
// -----------------------------------------------------------------------
(FILL)
    // Initialise addr to first word of box (SCREEN + 32*K = 16384 + 32 = 16416)
    @16416
    D=A
    @addr
    M=D             // addr = 16416

(FILLLOOP)
    // --- Stop condition: if addr >= 17056 we have drawn all 20 rows ---
    @17056
    D=A
    @addr
    D=D-M           // D = 17056 - addr
    @LOOP
    D;JLE           // if 17056 - addr <= 0  =>  addr >= 17056  =>  done

    // --- Write color to word 0 of current row (addr) ---
    @color
    D=M             // D = color value
    @addr
    A=M             // A = addr
    M=D             // RAM[addr] = color

    // --- Write color to word 1 of current row (addr + 1) ---
    @color
    D=M             // D = color value
    @addr
    D=M             // D = addr
    @1
    D=D+A           // D = addr + 1
    @tmp
    M=D             // tmp = addr + 1
    @color
    D=M             // D = color
    @tmp
    A=M             // A = addr + 1
    M=D             // RAM[addr+1] = color

    // --- Advance addr by 32 to move to the next screen row ---
    @addr
    D=M             // D = addr
    @32
    D=D+A           // D = addr + 32
    @addr
    M=D             // addr = addr + 32

    @FILLLOOP
    0;JMP           // repeat
