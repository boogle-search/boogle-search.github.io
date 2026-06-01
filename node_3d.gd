extends Node

@export var models: Array[Node3D]

func _ready():
	for model in models:
		generate_collisions(model)

func generate_collisions(node: Node):

	for child in node.get_children():

		if child is MeshInstance3D and child.mesh:

			var body := StaticBody3D.new()
			var collision := CollisionShape3D.new()

			collision.shape = child.mesh.create_trimesh_shape()

			body.add_child(collision)
			child.add_child(body)

		generate_collisions(child)
