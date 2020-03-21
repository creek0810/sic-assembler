FACT    START   0
LOOP    LDA     RESULT
        MUL     CNT
        STA     RESULT
        LDA     CNT
        ADD     ONE
        STA     CNT
        COMP    ENDLOOP
        JLT     LOOP
.data-area
ENDLOOP WORD    6
ONE     WORD    1
CNT     WORD    1
RESULT  WORD    1
.data-area
        END     LOOP
