# Data Stream Format For The Omni Entertainment System

## The Reader
The Following Are Signals For the Decoder
- 2 Pulldown Clicks: Enable Reader and Mute
- 1 Pullup Click: Start Reading
- 1 Pulldown Click: Stop & Process
- 2 Pullup Clicks: Disable Reader and Unmute

Bits are encoded in a special way, which is unknown

When the Reader is enabled and reading, there cannot be any other audio clips

## The Omni
### Start
The Omni Will Scan Both Channels For a `Round Ready` Message. Once Found, Audio Will Play Out of the Channel where that message was found. If the command was on the left, the left channel will activate

### During Rounds
The Omni will play audio out of one channel only, The Omni Will Play However Many Rounds The Cartage Specifies, This Is Counted On `Round Ready`, Not `Question Prompt`

## Opcodes
The Data Stream is used as Opcode Operand, after the initial pattern

A Data Stream May Embed Multiple Instructions

|Opcode|Operands|Name|Action|
|------|----|----|------|
|?|None|Yeild Until `Prompt/GO`|Halts The Playhead and Sound until the `Promt/GO` Button is pressed, The unit will also beep every 30 seconds to signal this|
|?|The Answer, Encoded as 4bit numbers 0-9|Set Answer|Sets The Answer, Does nothing until `Prompt Answers` Is ran|
|?|None|Stop Accepting|Stops Accepting Answers, This Will Turn The Displays To The Current Score|
|?|Scores as 4 4bit numbers from 0-15|Set Scores|Configures Scores For the Next question, Scores are fastest to slowest, based on the FIRST Key Press, Not Enter|
|?|Minimum Score as number|Prompt Answers|Prompts For Answers, This Blinks `--` On their displays, Stays Blank if Condition Not met
|?|None|Flash Winner|Flashes the display with the highest score,
|?|None|Update Scores|Updates the Scores
|?|Enables, each bit is a player|Set Display Status|Turns Displays On/Off, Omni Ignores Non-signed in player displays|
|?|None|End Game|Overrides the counter and ends the game|