import json
from pathlib import Path
from threading import RLock  # Changed to RLock
import os
import copy


class ConfigManager:
    _instance = None
    _lock = RLock()  # Use RLock to replace Lock, allowing re-acquisition in the same thread

    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        # First check if instance exists; if not, lock and initialize
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        # Prevent duplicate initialization
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        self._config_path = Path.home() / ".config" / "PaperTranslator" / "config.json"
        self._config_data = {}

        # Don't lock here since outer layer may already be locked (get_instance); RLock is safe anyway
        self._ensure_config_exists()

    def _ensure_config_exists(self, isInit=True):
        """Ensure config file exists; create default config if not"""
        # No need to explicitly lock again here for the same reason; method body calls _load_config(),
        # which locks internally. Since RLock is reentrant, it won't block.
        if not self._config_path.exists():
            if isInit:
                self._config_path.parent.mkdir(parents=True, exist_ok=True)
                self._config_data = {}  # Default config content
                self._save_config()
            else:
                raise ValueError(f"config file {self._config_path} not found!")
        else:
            self._load_config()

    def _load_config(self):
        """Load config from config.json"""
        with self._lock:  # Lock to ensure thread safety
            with self._config_path.open("r", encoding="utf-8") as f:
                self._config_data = json.load(f)

    def _save_config(self):
        """Save config to config.json"""
        with self._lock:  # Lock to ensure thread safety
            # Remove circular references and write
            cleaned_data = self._remove_circular_references(self._config_data)
            with self._config_path.open("w", encoding="utf-8") as f:
                json.dump(cleaned_data, f, indent=4, ensure_ascii=False)

    def _remove_circular_references(self, obj, seen=None):
        """Recursively remove circular references"""
        if seen is None:
            seen = set()
        obj_id = id(obj)
        if obj_id in seen:
            return None  # Encounter already processed object, treat as circular reference
        seen.add(obj_id)

        if isinstance(obj, dict):
            return {
                k: self._remove_circular_references(v, seen) for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [self._remove_circular_references(i, seen) for i in obj]
        return obj

    @classmethod
    def custome_config(cls, file_path):
        """Load config file using custom path"""
        custom_path = Path(file_path)
        if not custom_path.exists():
            raise ValueError(f"Config file {custom_path} not found!")
        # Lock
        with cls._lock:
            instance = cls()
            instance._config_path = custom_path
            # Pass isInit=False here; error if not exists; normal _load_config() if exists
            instance._ensure_config_exists(isInit=False)
            cls._instance = instance

    @classmethod
    def get(cls, key, default=None):
        """Get config value"""
        instance = cls.get_instance()
        # When reading, locking or not locking is fine. But for consistency, we lock before and after modifying config.
        # get will lock if saving is needed -> _save_config()
        if key in instance._config_data:
            return instance._config_data[key]

        # If key exists in environment variables, use it and write back to config
        if key in os.environ:
            value = os.environ[key]
            instance._config_data[key] = value
            instance._save_config()
            return value

        # If default is not None, set and save
        if default is not None:
            instance._config_data[key] = default
            instance._save_config()
            return default

        # Raise exception if not found
        # raise KeyError(f"{key} is not found in config file or environment variables.")
        return default

    @classmethod
    def set(cls, key, value):
        """Set config value and save"""
        instance = cls.get_instance()
        with instance._lock:
            instance._config_data[key] = value
            instance._save_config()

    @classmethod
    def get_translator_by_name(cls, name):
        """Get corresponding translator config by name"""
        instance = cls.get_instance()
        translators = instance._config_data.get("translators", [])
        for translator in translators:
            if translator.get("name") == name:
                return translator["envs"]
        return None

    @classmethod
    def set_translator_by_name(cls, name, new_translator_envs):
        """Set or update translator config by name"""
        instance = cls.get_instance()
        with instance._lock:
            translators = instance._config_data.get("translators", [])
            for translator in translators:
                if translator.get("name") == name:
                    translator["envs"] = copy.deepcopy(new_translator_envs)
                    instance._save_config()
                    return
            translators.append(
                {"name": name, "envs": copy.deepcopy(new_translator_envs)}
            )
            instance._config_data["translators"] = translators
            instance._save_config()

    @classmethod
    def get_env_by_translatername(cls, translater_name, name, default=None):
        """Get corresponding translator config by name"""
        instance = cls.get_instance()
        translators = instance._config_data.get("translators", [])
        for translator in translators:
            if translator.get("name") == translater_name.name:
                if translator["envs"][name]:
                    return translator["envs"][name]
                else:
                    with instance._lock:
                        translator["envs"][name] = default
                        instance._save_config()
                        return default

        with instance._lock:
            translators = instance._config_data.get("translators", [])
            for translator in translators:
                if translator.get("name") == translater_name.name:
                    translator["envs"][name] = default
                    instance._save_config()
                    return default
            translators.append(
                {
                    "name": translater_name.name,
                    "envs": copy.deepcopy(translater_name.envs),
                }
            )
            instance._config_data["translators"] = translators
            instance._save_config()
            return default

    @classmethod
    def delete(cls, key):
        """Delete config value and save"""
        instance = cls.get_instance()
        with instance._lock:
            if key in instance._config_data:
                del instance._config_data[key]
                instance._save_config()

    @classmethod
    def clear(cls):
        """Clear all config values and save"""
        instance = cls.get_instance()
        with instance._lock:
            instance._config_data = {}
            instance._save_config()

    @classmethod
    def all(cls):
        """Return all config items"""
        instance = cls.get_instance()
        # Only reading here; generally no lock needed, but can lock for safety
        return instance._config_data

    @classmethod
    def remove(cls):
        instance = cls.get_instance()
        with instance._lock:
            os.remove(instance._config_path)
