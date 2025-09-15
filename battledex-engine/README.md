BattleDex Engine

This library is the heart of the combat simulation for Project RogueDex.

It is designed to be completely headless and rules-agnostic. This means it knows nothing about Pokémon, graphics, or networking. Its only job is to provide a deterministic, event-driven framework for managing turn-based battles.
Core Concepts

    Battle: The main object that manages the state of a single combat encounter.

    Combatant: An interface for any entity that can participate in a battle.

    Action: An interface for any action a combatant can take (e.g., using a move, switching out).

    Event Queue: The central loop that processes actions and their consequences, generating a log of events that describes everything that happened in a turn.
