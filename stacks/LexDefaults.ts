import { VoiceEngine } from '@aws-sdk/client-lex-models-v2';

/**
 * Default values for the bots.
 * You can override this in the individual bot configuration.
 */
export const LexDefaults = {
  engine: 'neural' as VoiceEngine,
  idleSessionTtlInSeconds: 300,
  nluConfidenceThreshold: 0.4,

  /**
   * Slot elicitation interrupt
   */
  slotAllowInterrupt: true,
  /**
   * Slot elicitation retries
   */
  slotRetries: 3,
};
