import yaml
import logging
import os
import time
from jinja2 import Template, UndefinedError
import ce_actions

class WorkflowEngine:
    def __init__(self, adb_id, language, instance_name):
        self.adb_id = adb_id
        self.language = language
        self.context = {'instance_name': instance_name}
        self.actions = {
            'click': lambda args: ce_actions.click(self.adb_id, *args),
            'delay': lambda args: time.sleep(args),
            'scroll': lambda args: ce_actions.scroll(self.adb_id, *args),
            'send_email': lambda args: ce_actions.send_email("CE Automation Notification", self._render_template(args)),
            'log': lambda args: logging.info(f"[WORKFLOW] {self._render_template(args)}"),
            'emergency_exit': lambda args: ce_actions.emergency_exit(args)
        }
        self.conditional_actions = {
            'compare_with_image': lambda *args: ce_actions.compare_with_image(self.adb_id, self.language, self.context['instance_name'], *args),
            'compare_with_text': lambda *args: ce_actions.compare_with_text(self.adb_id, self.language, self.context['instance_name'], *args),
            'compare_with_any_image': lambda *args: ce_actions.compare_with_any_image(self.adb_id, self.language, self.context['instance_name'], *args),
            'compare_with_text_easyocr': lambda *args: ce_actions.compare_with_text_easyocr(self.adb_id, self.language, self.context['instance_name'], *args),
            'compare_with_features': lambda *args: ce_actions.compare_with_features(self.adb_id, self.language, self.context['instance_name'], *args),
            'get_coords_from_image': lambda *args: ce_actions.get_coords_from_image(self.adb_id, self.language, *args),
            'get_all_coords_from_image': lambda *args: ce_actions.get_all_coords_from_image(self.adb_id, self.language, *args),
            'get_coords_from_features': lambda *args: ce_actions.get_coords_from_features(self.adb_id, self.language, *args),
            'get_all_coords_from_features': lambda *args: ce_actions.get_all_coords_from_features(self.adb_id, self.language, *args)
        }

    def _render_template(self, template_string):
        """Renders a simple string template."""
        if not isinstance(template_string, str):
            return template_string
        # The context for rendering includes variables, callable functions, AND safe built-ins like len.
        # --- THIS IS THE FIX ---
        full_context = {**self.context, **self.conditional_actions, 'len': len}
        return Template(template_string).render(full_context)

    def _render_params(self, params):
        """
        Recursively renders Jinja2 templates in parameters.
        This function's job is to turn template strings into their final values.
        """
        if isinstance(params, str):
            # Render the string. If it contains a function call like get_coords,
            # it will be executed and its return value (e.g., a tuple) will be embedded.
            rendered_value = self._render_template(params)
            
            # After rendering, if the result is a string that LOOKS like a Python literal
            # (e.g., "(1, 2)", "['a', 'b']", "None"), we can evaluate it to get the object.
            try:
                # Use a safe eval to perform the conversion.
                return eval(rendered_value, {'__builtins__': {}}, {})
            except (SyntaxError, TypeError, NameError):
                # If eval fails, it was just a regular string. Return it as is.
                return rendered_value
        elif isinstance(params, list):
            return [self._render_params(item) for item in params]
        elif isinstance(params, dict):
            return {key: self._render_params(value) for key, value in params.items()}
        else:
            # Return numbers, booleans, etc. as-is
            return params

    def _evaluate_condition(self, condition_str):
        """
        Evaluates a condition string to True or False.
        This is the ONLY place that should perform logical evaluation.
        """
        logging.debug(f"Evaluating condition: {condition_str}")
        try:
            # The context for evaluation includes variables and callable functions.
            eval_globals = {'__builtins__': None}
            eval_locals = {**self.context, **self.conditional_actions}
            return eval(condition_str, eval_globals, eval_locals)
        except Exception as e:
            logging.error(f"Error evaluating condition '{condition_str}': {type(e).__name__}: {e}")
            return False

    def _process_steps(self, steps):
        if steps is None: 
            logging.error("A 'then' or 'do' block in the workflow is empty."); return
        for step in steps:
            if not isinstance(step, dict): 
                logging.error(f"Malformed step found in workflow: {step}"); continue
            
            command = list(step.keys())[0]
            raw_params = step[command]
            
            if raw_params is None and command not in ['if', 'while']:
                 logging.error(f"Malformed step: command '{command}' has no value."); continue

            # Handle structural commands first, using the raw condition string
            if command == 'if':
                if self._evaluate_condition(raw_params['condition']):
                    self._process_steps(raw_params.get('then'))
                elif 'else' in raw_params:
                    self._process_steps(raw_params.get('else'))
            elif command == 'while':
                while self._evaluate_condition(raw_params['condition']):
                    self._process_steps(raw_params.get('do'))
            
            # For all other "action" commands, render their parameters
            else:
                rendered_params = self._render_params(raw_params)
                
                if command in self.actions:
                    if isinstance(rendered_params, list) and command in ['click', 'scroll']:
                        self.actions[command](rendered_params)
                    else:
                        self.actions[command](rendered_params)
                elif command == 'set':
                    # set expects a dict, which _render_params will have handled
                    self.context.update(rendered_params)
                    logging.debug(f"Context updated: {self.context}")
                elif command == 'increment':
                    # Increment needs the raw key, which is a string
                    self.context[raw_params] = self.context.get(raw_params, 0) + 1
                    logging.debug(f"Incremented '{raw_params}': {self.context[raw_params]}")
                else:
                    logging.warning(f"Unknown command in workflow: {command}")


    def run_workflow(self, workflow_name):
        # ... (This function is unchanged) ...
        yaml_path = os.path.join("resources", self.language, "workflows.yaml")
        if not os.path.exists(yaml_path): logging.error(f"Workflow file not found for language '{self.language}': {yaml_path}"); return
        with open(yaml_path, 'r') as f: data = yaml.safe_load(f)
        target_scenario = next((s for s in data.get('scenarios', []) if s.get('name') == workflow_name), None)
        if not target_scenario: logging.error(f"Workflow '{workflow_name}' not found in {yaml_path}"); return
        if 'steps' not in target_scenario or not target_scenario['steps']: logging.error(f"Workflow '{workflow_name}' has no steps defined. Skipping."); return
        logging.info(f"Executing workflow: {workflow_name} - {target_scenario.get('description', '')}")
        self._process_steps(target_scenario['steps'])
        logging.info(f"Finished workflow: {workflow_name}")
    
     