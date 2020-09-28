from unittest.case import TestCase

from dispatch import Dispatch, MethodNotRegistered


class TestDispatch(TestCase):
    def test_register__should_register_only_prefix(self):
        class Endpoint:
            def no_register(self):
                pass

            def PREFIX_foo(self):
                pass

        target = Dispatch().register(Endpoint, 'PREFIX_')
        self.assertEqual(['foo'], list(target.registered.keys()))

    def test_simple_procedure_dispatch(self):
        class Endpoint:
            def __init__(self):
                self.called = False

            def API_pippo(self):
                self.called = True

        target = Dispatch().register(Endpoint, 'API_')
        instance = Endpoint()
        target.dispatch(instance, 'pippo')
        self.assertTrue(instance.called)

    def test_dispatch__should_not_call_late_added_method_AND_raise_exception(self):
        self.called = False

        def call_API_late():
            self.called = True

        class Endpoint:
            pass

        target = Dispatch().register(Endpoint, 'API_')
        instance = Endpoint()
        setattr(instance, 'API_late', lambda: call_API_late())

        self.assertRaises(MethodNotRegistered, lambda: target.dispatch(instance, 'late'))
        self.assertFalse(self.called)

    def test_dispatch__with_param_and_return_value(self):
        class Endpoint:
            def __init__(self):
                self.name = None

            def API_set_name(self, name):
                self.name = name
                return 'done'

        target = Dispatch().register(Endpoint, 'API_')
        instance = Endpoint()

        result = target.dispatch(instance, 'set_name', {'name': 'john'})
        self.assertEqual('john', instance.name)
        self.assertEqual('done', result)