Title: Infusion and JSON Schemas, Part 5: Reuse and Extension, Part Two
Date: 2018-03-27 15:30
Category: Code
Tags: JSON Schema
Slug: infusion-and-json-schema-reuse-two
Author: Tony Atkins <tony@raisingthefloor.org>
Summary: An updated discussion of the issues involved in reusing and extending JSON Schemas between components.

# Introduction #

Earlier in this series (late 2017), I wrote up some approaches to [extending and reusing JSON Schema
definitions]({filename}./reusing-and-extending.md), talking about how a child grade might modify the JSON Schema defined
by its parent or other more distant ancestors.

In other discussions, we have tended to err on the side of working with component options in the way we have in the
past, i.e. with full access to merging, expansion, options distribution, et cetera.  In this post, I will outline
various ways in which a child grade might wish to modify a parent schema, and illustrate how they might be handled with
a combination of options merging and `mergePolicy` rules.

The examples in this post will be using [draft v7](http://json-schema.org/draft-07/schema) of the JSON Schema standard.  If you have not worked
with JSON Schemas in a while, I would strongly encourage you to review the recent changes.

Although this is far from settled, for the purposes of these examples, I will assume that the top-level `schema`
option is used to define or modify the effective schema, as in this base grade I will use in most of the examples below:

```javascript
fluid.defaults("my.validatable.grade", {
    // This will more likely inherit from a base grade common to all schema-validated components.
    gradeNames: ["fluid.component"],
    schema: {
        "$schema": "http://json-schema.org/draft-07/schema",
        properties: {
            "name": {
                "type": "string",
                "minLength": 4
            }
        },
        required: ["name"]
    }
});
```

# Changing Values #

Changing individual values is simple to accomplish with options merging.  Say for example that we want to update the
`$schema` and test the merged schema against a different version of the JSON Schema draft standard.  We might create a
derived grade like the following:

```javascript
fluid.defaults("my.newer.grade", {
    gradeNames: ["my.validatable.grade"],
    schema: {
        "$schema": "http://json-schema.org/draft-06/schema"
    }
});
```

This offers the possibility to add a particular version of the draft standard to the base grade, and have that be
inherited by the "schema snippets" used in existing work.

# Adding Additional Properties #

Starting with the original base grade, options merging can also reasonably add new properties just through the default
options merging:

```javascript
fluid.defaults("my.grade.with.additional.properties", {
    gradeNames: ["my.validatable.grade"],
    schema: {
        properties: {
            "address": {
                "type": "string"
            }
        }
    }
});
```

The merged schema would effectively be:

```json
{
        "$schema": "http://json-schema.org/draft-07/schema",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 4
            },
            "address": {
                "type": "string"
            }
        },
        "required": ["name"]
    }
```

This basic example does not require the author to specify any hints about options merging in order to produce a valid
schema.

# Changing Types #

Let's say that we wish to evolve a free-form string inherited from a parent grade into a sub-object, i.e. to add more
structure to a previously unstructured field.  For example, we might wish to break out the previously defined `name`
field into sub-fields:

```javascript
fluid.defaults("my.grade.new.type.polluting", {
    gradeNames: ["my.validatable.grade"],
    schema: {
        "properties": {
            "name": {
                "type": "object",
                "properties": {
                    "first":  { "type": "string"},
                    "middle": { "type": "string"},
                    "last":   { "type": "string"}
                },
                "required": ["first", "last"]
            }
        }
    }
});
```

If we handle this using simple options merging, the resulting schema is polluted with the leftover `minLength` attribute:

```json
{
    "$schema": "http://json-schema.org/draft-07/schema",
    "properties": {
        "name": {
            "type": "object",
            "properties": {
                "first":  { "type": "string"},
                "middle": { "type": "string"},
                "last":   { "type": "string"}
            },
            "required": ["first", "last"],
            "minLength": 4
        }
    },
    "required": ["name"]
}
```

Although, some validators will ignore the additional material, many conform more closely to the standard and report the
schema itself as invalid.  This is where we start using `mergePolicy` hints to improve on the default merging:


```javascript
fluid.defaults("my.grade.new.type.clean", {
    gradeNames: ["my.validatable.grade"],
    mergePolicy: {
        "schema.properties.name": "replace"
    },
    schema: {
        "properties": {
            "name": {
                "type": "object",
                "properties": {
                    "first":  { "type": "string"},
                    "middle": { "type": "string"},
                    "last":   { "type": "string"}
                },
                "required": ["first", "last"]
            }
        }
    }
});
```

This ensures that the "name" attribute is completely replaced, and that the invalid straggling `minLength` value is not
preserved.

# Changing the "Required" Fields #

As shown in the above examples, the `required` attribute specifies the fields that must be contained as an array of
keys relative to their enclosing object.

```javascript
fluid.defaults("my.grade.required.nohints", {
    gradeNames: ["my.validatable.grade"],
    schema: {
        "required": []
    }
});
```

Depending on how familiar you are with array merging, you might be surprised at the results of the merge:

```json
{
    "$schema": "http://json-schema.org/draft-07/schema",
    "properties": {
        "name": {
            "type": "string",
            "minLength": 4
        }
    },
    "required": ["name"]
}
```

To properly replace the `required` attribute with an empty array, we need another hint, as in:

```javascript
fluid.defaults("my.grade.required.nohints", {
    gradeNames: ["my.validatable.grade"],
    mergePolicy: { "schema.required": "replace" },
    schema: {
        "required": []
    }
});
```

# Removing Properties Altogether #

Thus far we have dodged the issue of deleting material by using the "replace" merge strategy.  We have either entirely
replaced the object containing the material to be removed, or in the case of an array, replaced it with an empty array.

What if we want to remove an inherited property altogether?  Take this as our starting grade, and assume we want to
disallow the use of the `state` field:

```javascript
fluid.defaults("my.overly.verbose.grade", {
    // This will more likely inherit from a base grade common to all schema-validated components.
    gradeNames: ["fluid.component"],
    schema: {
        "$schema": "http://json-schema.org/draft-07/schema",
        properties: {
            "address":  { "type": "string"},
            "city":     { "type": "string"},
            "state":    { "type": "string"},
            "postCode": { "type": "string"}
        }
    }
});
```

We could for example mangle its definition so that it's not possible to ever enter the field correctly, as in:

```javascript
fluid.defaults("my.definition.mangling.grade", {
    gradeNames: ["my.overly.verbose.grade"],
    schema: {
        properties: {
            "state":    { "minLength": 3, "maxLength": 2}
        }
    }
});
```

This has the effect of making it impossible to use the option, but is not ideal, as in the case of UI generation, an
input might still be displayed onscreen.  How can we remove material using `mergePolicy` hints?

In addition to keywords like "nomerge", "noexpand", you can also [supply a function as the right side of a merge
policy](https://docs.fluidproject.org/infusion/development/OptionsMerging.html#structure-of-the-merge-policy-object).
One strategy I have explored [in this CodePen](https://codepen.io/the-t-in-rtf/pen/Zxaxrm?editors=1011) is to supply a
"noop" function for a given target path, which results in the material being removed, as in:


```javascript
fluid.defaults("my.definition.removing.grade", {
    gradeNames: ["my.overly.verbose.grade"],
    mergePolicy: {
        "schema.properties.state": function(){}
    }
});
```

This results in the removal of `schema.properties.state`, but does have implications for derived grades.  Once we extend
the above grade, it is impossible to supply a value for `schema.properties.state`, unless we add an implicit rule to
restore the merging of the variable, as in:

```javascript
fluid.defaults("my.definition.restoring.grade", {
    gradeNames: ["my.definition.removing.grade"],
    mergePolicy: {
        "schema.properties.state": "{that}.options.schema.properties.state"
    },
    schema: {
        properties: {
            state: { minLength: 2 }
        }
    }
});
```

The updated mergePolicy restores the underlying field removed by the intermediate grade, and will also allow us to merge
in additional options, both in the "restoring" grade, and in any derived grades.

# When and How to Validate #
  
In the upcoming ["Potentia II"](https://issues.fluidproject.org/browse/FLUID-6148) work on Infusion, we will gain
the ability to bind actions to early parts of the component lifecycle, and to  prevent component creation from
proceeding further if there are problems.  As Antranig hinted at in a previous meeting, we might use this to bind one or
more validation passes.  At a minimum, I would propose making two passes:

1. Validating the merged, expanded schema definition itself.
2. Validating the component options against the schema.

The first step would immediately and dramatically make it clear to authors when they have merged material in a way that
requires the addition of `mergePolicy` rules.

# Conclusion #

Although this draft outlines a handful of ways we might proceed, it's meant as a starting point for discussion.  I will
write up the conclusions we reach and proceed to sketch out "schema validated components" based on what we agree.
 
